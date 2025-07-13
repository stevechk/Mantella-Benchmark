from typing import Any, Dict, List
import os
import json
import requests
import time
import re

from scorer import Scorer


class OpenRouterScorer(Scorer):

    def __init__(self, model: str):
        self.api_key=os.getenv("OPENROUTER_API_KEY")
        if self.api_key is None or self.api_key == "":
            raise Exception("OPENROUTER_API_KEY is not set")
        self.model = model

    def score(self, model_name: str, test_name: str, questions: List[List[Dict[str, Any]]], references: List[str], candidates: List[str]) -> List[float]:

        scores = []
        for i, question in enumerate(questions):

            percentage_progress = (i * 100) / (len(questions))
            print(f"\rScoring progress: {percentage_progress:.2f}% ...", end="", flush=True)
            
            question_text = question[len(question) - 1]['content']
            initial_prompts = json.dumps(question[:-1])
            message = f"For the question, \"{question_text}\", and the initial prompts: \"{initial_prompts}\", rate the following response on a scale of 0-10, replying with just your numerical score in brackets like [8], and then including your reasoning: \"{candidates[i]}\""

            max_retries = 5
            retry_delay = 60  # 1 minute in seconds
            for attempt in range(max_retries):
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    data=json.dumps({
                        "model": self.model,
                        "messages": [
                        {
                            "role": "user",
                            "content": f"{message}"
                        }
                        ]
                    })
                )

                if not response.status_code in [400, 429, 500, 502]:  # Not rate limited
                    break
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    print(f"Rate limited, waiting {retry_delay} seconds before retrying")
                    time.sleep(retry_delay)  # Wait 1 minute before retrying

            #check if the response is valid
            if response.status_code != 200:
                print(f"Failed to score question {i}: {response.status_code} {response.text}")
                score = 0.0
                scores.append(score)
                continue

            #remove any non-numeric characters
            try:
                response_json = response.json()
                response_text = response_json['choices'][0]['message']['content']
                
                # Extract first number between square brackets using regex
                match = re.search(r'\[(.*?)\]', response_text)
                if match:
                    score = float(match.group(1))/10.0
                else:
                    # Fallback to old behavior if no brackets found
                    response_text_cleaned = re.sub(r'[^0-9]', '', response_text)
                    score = float(response_text_cleaned)/10.0
            except ValueError:
                print(f"Failed to parse score from response: {response_text}")
                score = 0.0
            except Exception as e:
                print(f"Unexpected error parsing score: {e}")
                score = 0.0

            scores.append(score)

        print()
        return scores
    
    def shutdown(self):
        return
