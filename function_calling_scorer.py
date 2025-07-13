import json
from typing import Any, Dict, List
from scorer import Scorer

class FunctionCallingScorer(Scorer):
    def __init__(self):
        pass
    
    def score(self, model_name: str, test_name: str, questions: List[List[Dict[str, Any]]], references: List[str], candidates: List[str]) -> List[float]:
        scores = []

        # expect message in format: <tool_call>
        # {'title': 'FunctionCall', 'type': 'object', 'properties': {'name': {'title': 'Name', 'type': 'string'},
        # 'arguments': {'title': 'Arguments', 'type': 'object'}}, 'required': ['arguments', 'name']}
        # </tool_call>

        for i, question in enumerate(questions):

            question_text = question[len(question) - 1]['content']
            response_text = candidates[i]

            # change blocks that are markdown format e.g (```json... ```) to xml (<tool_call></tool_call>)
            if '```json' in response_text:
                response_text = response_text.replace('```json', '<tool_call>').replace('```', '</tool_call>')
            elif response_text.count('```') > 1:
                response_text = response_text.replace('```', '<tool_call>', 1)
                response_text = response_text.replace('```', '</tool_call>', 1)

                if response_text.count('```') > 0:
                    # just return the first tool call block
                    response_text = response_text.split('</tool_call>')[0] + '</tool_call>'


            score = 0.0
            if question_text == references[i]:
                score = 1.0
            else:

                if "<tool_call>" not in references[i]:
                    # if we dont expect a tool call, as long as the candidate doesnt include a tool call block, we can ignore the rest of the text

                    if "<tool_call>" not in response_text:
                        score = 1.0
                    else:
                        score = 0.0

                elif "<tool_call>" in references[i]:

                    reference_between_tags = references[i].split("<tool_call>")[1].split("</tool_call>")[0]

                    if "<tool_call>" in response_text:
                        candidate_between_tags = response_text.split("<tool_call>")[1].split("</tool_call>")[0]
                    else:
                        candidate_between_tags = response_text # try to interpret the whole response as a tool call

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

        return matches
        
    except (json.JSONDecodeError, TypeError, ValueError):
        print(f"Error comparing JSON strings: Candidate: {candidate_str}, Reference: {reference_str}")
        return False 