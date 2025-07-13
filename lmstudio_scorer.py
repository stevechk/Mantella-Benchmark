import json
import re
from typing import Any, Dict, List

from scorer import Scorer
from lmstudio_control import LmStudioModel

class LmStudioScorer(Scorer):
    def __init__(self, endpoint: str, model: str):
        self.model = LmStudioModel(endpoint, model)

    def score(self, model_name: str, test_name: str, questions: List[List[Dict[str, Any]]], references: List[str], candidates: List[str]) -> List[float]:
        self.model.load()

        scores = []
        for i, question in enumerate(questions):

            question_text = question[len(question) - 1]['content']
            initial_prompts = json.dumps(question[:-1])
            scoring_message = f"For the question, \"{question_text}\", and the initial prompts: \"{initial_prompts}\", rate the following response on a scale of 0-10, replying with just your numerical score in brackets like [8], and then including your reasoning: \"{candidates[i]}\""

            response_text = self.model.call(scoring_message)

            #remove any non-numeric characters
            try:
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

        self.model.unload()
        return scores
    
    def shutdown(self):
        return