from typing import Any, Dict, List
import os
import json
import requests
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from scorer import Scorer


class RateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_rate_limit_time = 0
        self.rate_limit_delay = 60  # 1 minute in seconds
    
    def handle_rate_limit(self):
        with self.lock:
            current_time = time.time()
            time_since_last_limit = current_time - self.last_rate_limit_time
            
            if time_since_last_limit < self.rate_limit_delay:
                # Need to wait for the remaining time
                wait_time = self.rate_limit_delay - time_since_last_limit
                print(f"Rate limit detected. All threads waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            
            self.last_rate_limit_time = time.time()
            print("Resuming after rate limit cooldown...")


class OpenRouterScorer(Scorer):

    def __init__(self, model: str):
        self.api_key=os.getenv("OPENROUTER_API_KEY")
        if self.api_key is None or self.api_key == "":
            raise Exception("OPENROUTER_API_KEY is not set")
        self.model = model
        self.rate_limiter = RateLimiter()

    def score(self, model_name: str, test_name: str, questions: List[List[Dict[str, Any]]], references: List[str], candidates: List[str]) -> List[float]:

        def process_question(args):
            i, question, candidate = args
            
            question_text = question[len(question) - 1]['content']
            initial_prompts = json.dumps(question[:-1])
            message = f"For the question, \"{question_text}\", and the initial prompts: \"{initial_prompts}\", rate the following response on a scale of 0-10, replying with just your numerical score in brackets like [8], and then including your reasoning: \"{candidate}\""

            max_retries = 5
            for attempt in range(max_retries):
                try:
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

                    # Check if we hit a rate limit
                    if response.status_code in [429]:  # Rate limited
                        self.rate_limiter.handle_rate_limit()
                        continue  # Retry immediately after cooldown
                    elif response.status_code in [400, 500, 502]:  # Other errors
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Short delay for other errors
                            continue
                        else:
                            break
                    else:
                        # Success or non-retryable error
                        break

                except Exception as e:
                    print(f"Request failed for question {i}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return i, 0.0

            #check if the response is valid
            if response.status_code != 200:
                print(f"Failed to score question {i}: {response.status_code} {response.text}")
                return i, 0.0

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

            return i, score

        # Prepare arguments for parallel processing
        args_list = [(i, question, candidates[i]) for i, question in enumerate(questions)]
        
        # Use ThreadPoolExecutor for parallel processing
        # Use max_workers=5 to avoid overwhelming the API
        scores = [0.0] * len(questions)  # Initialize with default scores
        completed = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all tasks
            future_to_index = {executor.submit(process_question, args): args[0] for args in args_list}
            
            # Process completed tasks
            for future in as_completed(future_to_index):
                index, score = future.result()
                scores[index] = score
                completed += 1
                
                # Update progress
                percentage_progress = (completed * 100) / len(questions)
                print(f"\rScoring progress: {percentage_progress:.2f}% ...", end="", flush=True)

        print()
        return scores
    
    def shutdown(self):
        return
