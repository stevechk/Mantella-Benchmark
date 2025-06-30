import statistics
import sys
import yaml
from pathlib import Path
import os

from remote_llm_model import RemoteLLMModel

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from lmstudio_control import LmStudioModel
from scorers import FunctionCallingScorer, Scorer
from utils import Timer

class InputResponsePair:
    def __init__(self, input: str, expected_response: str):
        self.input = input
        self.expected_response = expected_response
        self.actual_response = None

class TestRunData:
    def __init__(self, name: str, data: list[InputResponsePair]):
        self.name = name
        self.data = data


def load_test_data_from_yaml(yaml_file_path: str = "test_data.yaml"):
    """
    Load all test run data from a YAML file.
    
    Args:
        yaml_file_path: Path to the YAML file containing test data
        
    Returns:
        List of TestRunData objects
    """
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        test_data_list = []
        
        for test_run in data.get('test_runs', []):
            test_data = []
            for item in test_run.get('data', []):
                test_data.append(InputResponsePair(
                    input=item['input'],
                    expected_response=item['expected_response']
                ))
            
            test_data_list.append(TestRunData(
                name=test_run['name'],
                data=test_data
            ))
        
        return test_data_list
    
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file_path}' not found.")
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return []
    except KeyError as e:
        print(f"Error: Missing required key in YAML file: {e}")
        return []

def load_config_from_yaml(yaml_file_path: str = "test_data.yaml"):
    """
    Load configuration data from a YAML file.
    
    Args:
        yaml_file_path: Path to the YAML file containing configuration
        
    Returns:
        Dictionary containing configuration data
    """
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        config = data.get('config', {})
        
        # Override model_api_key with environment variable if set
        env_api_key = os.getenv('OPENROUTER_API_KEY')
        if env_api_key:
            config['model_api_key'] = env_api_key
        
        return config
    
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file_path}' not found.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return {}

def main():

    # Load configuration from YAML
    config = load_config_from_yaml()
    test_iterations = config.get('test_iterations', 10)
    model_list = config.get('models', [])
    prompt_template = config.get('prompt_template', "")
    data_template = config.get('data_template', "")
    model_type = config.get('model_type', "lmstudio")
    model_endpoint = config.get('model_endpoint', "")
    model_api_key = config.get('model_api_key', "")

    # Load test data from YAML
    test_data_list = load_test_data_from_yaml()

    scorer = FunctionCallingScorer()

    #create a csv file to store the results
    results_file = "results.csv"
    with open(results_file, "w") as f:
        f.write("Model,Test,Min,Max,Average,Average Inference Time\n")

    for model_name in model_list:

        if model_type == "lmstudio":
            model = LmStudioModel(model_endpoint, model_name, context_length=8192)
        elif model_type == "remote":
            model = RemoteLLMModel(model_endpoint, model_api_key, model_name)

        with Timer("Model load time"):
            # print error on failure, but continue to next model
            try:
                model.load()
            except Exception as e:
                print(f"Error loading model {model_name}: {e}")
                continue

        for test_data_set in test_data_list:

            print(f"Model: {model_name}, Test: {test_data_set.name}")
            print(f"--------------------------------")

            questions = []
            references = []
            candidates = []

            with Timer("Model inference") as model_inference_time:
                for i in range(test_iterations):
                    for question_index, question in enumerate(test_data_set.data):

                        percentage_progress = ((i * len(test_data_set.data) + question_index) * 100) / (test_iterations * len(test_data_set.data))
                        print(f"\rProgress: {percentage_progress:.2f}%", end="", flush=True)

                        prompt_template_str = str(prompt_template)
                        data_template_str = str(data_template)
                        question_input_str = str(question.input)

                        question_message = [
                            {"role": "system", "content": prompt_template_str}, 
                            {"role": "user", "content": data_template_str},
                            {"role": "user", "content": question_input_str}
                        ]
                        
                        response_text = ""

                        try:
                            response_text = model.call_with_messages(question_message)
                        except Exception as e:
                            print(f"Error calling model {model_name}: {e}")
                            continue
                        
                        #ignore thinking part of response for models such as DeepSeek R1
                        if '</think>' in response_text:
                            response_text = response_text.split('</think>')[1]

                        # change blocks that are markdown format e.g (```json... ```) to xml (<tool_call></tool_call>)
                        if '```json' in response_text:
                            response_text = response_text.replace('```json', '<tool_call>').replace('```', '</tool_call>')
                        elif response_text.count('```') > 1:
                            response_text = response_text.replace('```', '<tool_call>', 1)
                            response_text = response_text.replace('```', '</tool_call>', 1)

                            if response_text.count('```') > 0:
                                # just return the first tool call block
                                response_text = response_text.split('</tool_call>')[0] + '</tool_call>'

                        assert response_text is not None

                        questions.append(question_input_str)
                        candidates.append(response_text)
                        references.append(question.expected_response)

            try:
                print()
                with Timer("Scoring"):
                    scores = scorer.score(model_name=model_name, test_name=test_data_set.name, questions=questions, references=references, candidates=candidates)
            except Exception as e:
                print(f"Error scoring model {model_name}: {e}")
                continue

            if not (isinstance(scores, list) and len(scores) == len(test_data_set.data)*test_iterations):
                print(f"Error: scores not populated by scorer for {model_name} for test {test_data_set.name}")
                continue

            #get min, max, and average score
            min_score = min(scores)
            max_score = max(scores)
            average_score = sum(scores) / len(scores)
            average_inference_time = model_inference_time.elapsed_time / (test_iterations * len(test_data_set.data))

            print(f"Max score: {max_score}, Min score: {min_score}, Average score: {average_score}, Model inference time: {average_inference_time:.2f} seconds")

            print(f"================================================")

            #write the results to the csv file
            with open(results_file, "a") as f:
                f.write(f"{model_name},{test_data_set.name},{min_score},{max_score},{average_score},{average_inference_time:.2f}\n")

        model.unload()

    scorer.shutdown()


if __name__ == "__main__":

    with Timer("Total execution time"):
        main()
