# Mantella-Benchmark
A simple benchmarking tool for benchmarking Large Language Models (LLMs) for use with function calling (also known as 'tool calling') tasks in the Mantella Skyrim/Fallout4 mod.


## Current Leaderboard

| Base Model  | Model                                                                                         | Deployment Type | Size (if local) | Average Score (out of 1) | Average Call Time (seconds) | Cost         |
| ----------- | --------------------------------------------------------------------------------------------- | --------------- | --------------- | ------------------------ | --------------------------- | ------------ |
| Qwen 2.5    | Mungert/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-q4_k_l.gguf                        | local           | 5.09 GB         | 0.878                    | 0.87                        | Free (local) |
| Gemma 3     | lmstudio-community/gemma-3-4B-it-qat-GGUF/gemma-3-4B-it-QAT-Q4_0.gguf                         | local           | 3.21 GB         | 0.850                    | 0.61                        | Free (local) |
| Qwen 2.5    | Qwen/Qwen2.5-7B-Instruct-GGUF/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf                    | local           | 8.10 GB         | 0.850                    | 7.85                        | Free (local) |
| Gemma 3     | lmstudio-community/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q8_0.gguf                                 | local           | 4.98 GB         | 0.835                    | 0.79                        | Free (local) |
| Qwen 2.5    | lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf             | local           | 4.68 GB         | 0.821                    | 0.90                        | Free (local) |
| Qwen 3      | lmstudio-community/Qwen3-1.7B-GGUF/Qwen3-1.7B-Q8_0.gguf                                       | local           | 2.17 GB         | 0.778                    | 2.01                        | Free (local) |
| GPT-4o-mini | openai/gpt-4o-mini                                                                            | OpenRouter      |                 | 0.750                    | 1.40                        | $            |
| Gemma 3     | google/gemma-3-27b-it:free                                                                    | OpenRouter      |                 | 0.607                    | 4.52                        | Free         |
| Qwen 3      | qwen/qwen3-32b:free                                                                           | OpenRouter      |                 | 0.607                    | 9.76                        | Free         |
| Gemma 3     | lmstudio-community/gemma-3-12B-it-qat-GGUF/gemma-3-12B-it-QAT-Q4_0.gguf                       | local           | 7.74 GB         | 0.528                    | 6.07                        | Free (local) |
| Llama 3     | lmstudio-community/Meta-Llama-3-8B-Instruct-BPE-fix-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf | local           | 4.92 GB         | 0.528                    | 1.49                        | Free (local) |
| Mistral     | mistralai/mistral-small-3.2-24b-instruct:free                                                 | OpenRouter      |                 | 0.357                    | 3.23                        | Free         |
| Gemini 2.5  | google/gemini-2.5-pro                                                                         | OpenRouter      |                 | 0.357                    | 8.96                        | $$$          |
| Llama 3     | lmstudio-community/Meta-Llama-3-8B-Instruct-BPE-fix-GGUF/Meta-Llama-3-8B-Instruct-Q8_0.gguf   | local           | 8.54 GB         | 0.307                    | 19.99                       | Free (local) |
| Gemma 3     | lmstudio-community/gemma-3-1B-it-QAT-GGUF/gemma-3-1B-it-QAT-Q4_0.gguf                         | local           | 720 MB          | 0.207                    | 1.34                        | Free (local) |

Notes:
- Tests were run with default model parameters (e.g. temperature)
- The local models reference the LMStudio/HuggingFace link. 
- All local inference was run on a 3070ti (8gb VRAM) under Windows 11. 
- OpenAI models have a specific tool protocol that is not currently supported by this benchmark, so OpenAI results may be higher than indicated.
- Models format results in different ways (even when instructed to follow a standard). Some reasonable attempts have been made at parsing results before comparing.
- `test_iterations` is set to 10 to get a good balance of results

## Background

Function calling requires the LLM to understand natural language commands and convert them into structured function calls.

For example, the player might say to an NPC : "go and loot some weapons from the nearby chest". The LLM needs to turn this into the 'npc_loot_items' call, and identify that the player specifically wants 'weapons'. In this case, the expected_response would be: `"<tool_call>{'name': 'npc_loot_items', 'arguments': {'item_mode': 'weapons'}}</tool_call>"`

This use case typically requires LLMs that have been trained to do this, and correctly format the result.

## Features
- **Support either local (LMStudio) or remote models**
- **Configurable Test Data**: YAML-based configuration for easy test case management (via `test_data.yaml`)
- **Performance Metrics**: Scoring and timing analysis

## Benchmark installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Mantella-Benchmark
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows Powershell:
     ```powershell
     & venv\Scripts\activate.ps1
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## LLM Installation

### For Local Models (LM Studio)

1. **Install LM Studio**: Download and install [LM Studio](https://lmstudio.ai/)
2. **Install LM Studio CLI**: Follow the [CLI installation guide](https://docs.lmstudio.ai/cli/)
3. **Download Models**: Use the LM Studio interface or CLI to download models
4. **Configure test_data.yaml**:
   ```yaml
   config:
     model_type: "lmstudio"
     model_endpoint: "http://127.0.0.1:1234"
     models:
       - "lmstudio-community/gemma-3-12B-it-qat-GGUF/gemma-3-12B-it-QAT-Q4_0.gguf"
   ```

### For Remote Models (e.g. OpenRouter)

1. **Get API Key**: Sign up at [OpenRouter](https://openrouter.ai/) and get an API key
2. **Set Environment Variable**:
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```
3. **Configure test_data.yaml**:
   ```yaml
   config:
     model_type: "remote"
     model_endpoint: "https://openrouter.ai/api"
     models:
       - "mistralai/mistral-small-3.2-24b-instruct:free"
       - "google/gemma-3-27b-it:free"
   ```

## Usage

### Running the Benchmark

```bash
python function_calling_benchmark.py
```

The benchmark will:
1. Load each configured model
2. Run test cases multiple times (configurable in test_data.yaml via `test_iterations`)
3. Score the responses, and output results to `results.csv`
4. Dump any failures to `responses.txt` for further investigation

### Test Data Configuration

The `test_data.yaml` file contains:

- **Test Cases**: Input/output pairs for function calling scenarios
- **Model Configuration**: Which models to test and how to connect to them
- **Prompt Templates**: System prompts and data templates for the models
- **Function Definitions**: Available functions that models can call

### Example Test Case

```yaml
test_runs:
  - name: "function_calling"
    data:
      - input: "lets move over to talk to Charlie"
        expected_response: "<tool_call>{'name': 'move_character_near_npc', 'arguments': {'npc_name': ['Charlie'], 'npc_distance': [3.402], 'target_npc_id': ['1231']}}</tool_call>"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- Built for the Mantella gaming AI project (https://art-from-the-machine.github.io/Mantella), specfically function calling by (https://github.com/yetAnotherModder)
- Uses LM Studio for local model inference (https://lmstudio.ai/)
- Integrates with OpenRouter for remote model access (https://openrouter.ai/)