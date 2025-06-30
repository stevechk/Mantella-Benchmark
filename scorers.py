import json
from abc import ABC, abstractmethod
from typing import List


class Scorer(ABC):
    """Abstract base class for model response scorers."""
    
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def score(self, model_name: str, test_name: str, questions: List[str], references: List[str], candidates: List[str]) -> List[float]:
        pass
    
    @abstractmethod
    def shutdown(self):
        pass


class FunctionCallingScorer(Scorer):
    def __init__(self):
        pass
    
    def score(self, model_name: str, test_name: str, questions: List[str], references: List[str], candidates: List[str]) -> List[float]:
        scores = []

        # expect message in format: <tool_call>
        # {'title': 'FunctionCall', 'type': 'object', 'properties': {'name': {'title': 'Name', 'type': 'string'},
        # 'arguments': {'title': 'Arguments', 'type': 'object'}}, 'required': ['arguments', 'name']}
        # </tool_call>
        
        for i, question in enumerate(questions):

            score = 0.0
            if question == references[i]:
                score = 1.0
            else:

                if "<tool_call>" not in references[i]:
                    # if we dont expect a tool call, as long as the candidate doesnt include a tool call block, we can ignore the rest of the text

                    if "<tool_call>" not in candidates[i]:
                        score = 1.0
                    else:
                        score = 0.0

                elif "<tool_call>" in references[i]:

                    reference_between_tags = references[i].split("<tool_call>")[1].split("</tool_call>")[0]

                    if "<tool_call>" in candidates[i]:
                        candidate_between_tags = candidates[i].split("<tool_call>")[1].split("</tool_call>")[0]
                    else:
                        candidate_between_tags = candidates[i] # try to interpret the whole response as a tool call

                    if candidate_between_tags == reference_between_tags:
                        score = 1.0
                    else:
                        try:
                            # Use the helper function for robust JSON comparison
                            if compare_json_strings(candidate_between_tags, reference_between_tags):
                                score = 1.0
                            else:
                                score = 0.0
                        except Exception as e:
                            print(f"Error comparing JSON: {e}")
                            print(f"Candidate: {candidate_between_tags}")
                            print(f"Reference: {reference_between_tags}")
                            score = 0.0

            scores.append(score)

            # dump failures for further analysis
            if score < 1.0:
                with open("responses.txt", "a", encoding='utf-8') as f:
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Question: {question}\n")
                    f.write(f"Reference: {references[i]}\n")
                    f.write(f"Candidate: {candidates[i]}\n")
                    f.write(f" = Score: {score}\n")
                    f.write(f"--------------------------------\n")

        return scores
    
    def shutdown(self):
        pass


def compare_json_strings(candidate_str: str, reference_str: str) -> bool:
    """
    Compare two JSON strings, handling various formatting differences.
    Returns True if they represent the same data, False otherwise.
    """
    try:
        # Normalize quotes and whitespace
        candidate_normalized = candidate_str.replace("'", '"').strip()
        reference_normalized = reference_str.replace("'", '"').strip()
        
        # Parse JSON
        candidate_json = json.loads(candidate_normalized)
        reference_json = json.loads(reference_normalized)
        
        # Compare as sorted JSON strings to handle key order differences
        candidate_sorted = json.dumps(candidate_json, sort_keys=True, separators=(',', ':'))
        reference_sorted = json.dumps(reference_json, sort_keys=True, separators=(',', ':'))
        
        matches = (candidate_sorted == reference_sorted)

        if not matches:
            with open("responses.txt", "a", encoding='utf-8') as f:
                f.write(f"JSON MISMATCH: {candidate_sorted} != {reference_sorted}\n")

        return matches
        
    except (json.JSONDecodeError, TypeError, ValueError):
        print(f"Error comparing JSON strings: Candidate: {candidate_str}, Reference: {reference_str}")
        return False 