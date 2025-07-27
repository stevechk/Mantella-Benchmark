import sys
import yaml
from pathlib import Path
import os

from lmstudio_scorer import LmStudioScorer
from openrouter_scorer import OpenRouterScorer
from remote_llm_model import RemoteLLMModel

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from lmstudio_model import LmStudioModel
from function_calling_scorer import FunctionCallingScorer, Scorer
from utils import Timer

def load_config_from_yaml(yaml_file_path):
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        config = data.get('config', {})
        return config
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file_path}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

def main():

    # Load configuration from YAML
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <config_file>")
        print("Example: python benchmark.py tests/function_test_data.yaml")
        sys.exit(1)

    test_config_file = sys.argv[1]
    config = load_config_from_yaml(test_config_file)
    if config is None:
        sys.exit(1)

    test_iterations = config.get('test_iterations', 10)
    model_list = config.get('models', [])
    model_type = config.get('model_type', "lmstudio")
    model_endpoint = config.get('model_endpoint', "")
    test_suites = config.get('test_suites', [])

    # Override model_api_key with environment variable if set
    model_api_key = ""
    env_api_key = os.getenv('OPENROUTER_API_KEY')
    if env_api_key:
        model_api_key = env_api_key        

    #create a csv file to store the results
    results_file = "results.csv"
    with open(results_file, "w") as f:
        f.write("Model,Test,Min,Max,Average,Average Inference Time\n")

    with open("responses.txt", "w", encoding='utf-8') as f:
        f.write("")

    for model_name in model_list:
        for test_suite in test_suites:

            test_suite_name = list(test_suite.keys())[0]

            print(f"===================================================")
            print(f"Model: {model_name}, Test Suite: {test_suite_name}")

            # Load model and run inference
            model = None
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

            scorer_config = test_suite[test_suite_name]['scorer']

            if scorer_config is None:
                raise Exception(f"Scorer not configured for test suite {test_suite_name}")

            questions = []
            references = []
            candidates = []

            with Timer("Model inference") as model_inference_time:
                for i in range(test_iterations):
                    
                    tests = test_suite[test_suite_name]['tests']
                    for test_index, test in enumerate(tests):

                        percentage_progress = ((i * len(tests) + test_index) * 100) / (test_iterations * len(tests))
                        print(f"\rInference progress: {percentage_progress:.2f}% ...", end="", flush=True)

                        test_messages = []
                        for prompt in test_suite[test_suite_name]['setup_prompts']:
                            prompt_type = list(prompt.keys())[0]
                            prompt_content = str(prompt[prompt_type])
                            test_messages.append({"role": prompt_type, "content": prompt_content})
                        test_messages.append({"role": "user", "content": test['input']})

                        response_text = ""
                        try:
                            response_text = model.call_with_messages(test_messages)
                        except Exception as e:
                            print(f"Error calling model {model_name}: {e}")
                            response_text = "Error calling model"
                            continue
                        
                        #ignore thinking part of response for models such as DeepSeek R1
                        if '</think>' in response_text:
                            response_text = response_text.split('</think>')[1]

                        assert response_text is not None

                        questions.append(test_messages)
                        candidates.append(response_text)
                        references.append(test['expected_response'])

                print()

            if model is not None:
                model.unload()

            # Score the model
            try:
                scorer: Scorer = None
                if scorer_config['type'] == "FunctionCallingScorer":
                    scorer = FunctionCallingScorer()
                elif scorer_config['type'] == "OpenRouterScorer":
                    scorer = OpenRouterScorer(scorer_config['model'])
                elif scorer_config['type'] == "LmStudioScorer":
                    scorer = LmStudioScorer(scorer_config['endpoint'], scorer_config['model'])
                else:
                    raise Exception(f"Scorer {scorer_config['type']} not implemented")

                with Timer("Scoring"):
                    scores = scorer.score(model_name=model_name, test_name=test_suite_name, questions=questions, references=references, candidates=candidates)

                scorer.shutdown()
                    
            except Exception as e:
                print(f"Error scoring model {model_name}: {e}")
                continue

            if not (isinstance(scores, list) and len(scores) == len(tests)*test_iterations):
                print(f"Error: scores not populated by scorer for {model_name} for test {test_suite_name}")
                continue

            # dump failures for further analysis
            for i, score in enumerate(scores):
                if score < 0.5:
                    with open("responses.txt", "a", encoding='utf-8') as f:
                        f.write(f"Model: {model_name}\n")
                        f.write(f"Question: {questions[i]}\n")
                        f.write(f"Reference: {references[i]}\n")
                        f.write(f"Candidate: {candidates[i]}\n")
                        f.write(f" = Score: {score}\n")
                        f.write(f"--------------------------------\n")

            #get min, max, and average score
            min_score = min(scores)
            max_score = max(scores)
            average_score = sum(scores) / len(scores)
            average_inference_time = model_inference_time.elapsed_time / (test_iterations * len(tests))

            print(f"Max score: {max_score}, Min score: {min_score}, Average score: {average_score}, Model inference time: {average_inference_time:.2f} seconds")

            print()

            #write the results to the csv file
            with open(results_file, "a") as f:
                f.write(f"{model_name},{test_suite_name},{min_score},{max_score},{average_score},{average_inference_time:.2f}\n")


if __name__ == "__main__":
    with Timer("Total execution time"):
        main()
