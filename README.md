# Mantella-Benchmark
A simple benchmarking tool for benchmarking Large Language Models (LLMs) for use with the [Mantella Skyrim/Fallout4 mod.](https://art-from-the-machine.github.io/Mantella/)


## Current Leaderboard

### Function testing
This test evaluates function calling (also known as tool calling) LLMs. Scores and times are averaged across both single & multi NPC benchmarks.

| Base Model  | Model                                                                  | Deployment Type | Size (if local) | Average Score | Average Call Time (seconds) | Cost         | Comments                                                                                    |
| ----------- | ---------------------------------------------------------------------- | --------------- | --------------- | ------------- | --------------------------- | ------------ | ------------------------------------------------------------------------------------------- |
| Qwen 3      | qwen/qwen3-coder                                                       | OpenRouter      |                 | 94%           | 2.5                         | $1.50+ pm    | Best performance, but relatively slow and fairly expensive                                  |
| Qwen 2.5    | qwen2.5-coder-32b-instruct                                             | local           | 19.85 GB        | 84%           | 2.47                        | Free (local) | Best performing local model, but slow and at 20 GB its too large for most normal gaming PCs |
| GPT-4o-mini | openai/gpt-4o-mini                                                     | OpenRouter      |                 | 83%           | 1.45                        | $0.75 pm     | Good all-rounder if you dont have enough VRAM to run a local model                          |
| Qwen 3      | lmstudio-community/Qwen3-1.7B-GGUF/Qwen3-1.7B-Q8_0.gguf                | local           | 2.17 GB         | 82%           | 2.475                       | Free (local) | Excellent performer, especially for the size. Can likely run on most PCs                    |
| Qwen 2.5    | Mungert/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-q4_k_l.gguf | local           | 5.09 GB         | 80%           | 0.625                       | Free (local) | Fast local model. Good all-rounder                                                          |
| Qwen 2.5    | qwen2.5-coder-14b-instruct                                             | local           | 8.99 GB         | 78%           | 0.99                        | Free (local) | Mungert/Qwen2.5-7B-Instruct-1M-GGUF is faster, higher performing and uses less VRAM         |

Notes:
- Only models that consistently score > 75% average are listed.
- Tests were run with default model parameters (e.g. temperature).
- The local models reference the exact LMStudio/HuggingFace model and quant that was used.
- All local inference was run on a 3090 (24gb VRAM) under Windows 11. 
- OpenAI models have a specific tool protocol that is not currently supported by this benchmark, so OpenAI results may be higher than indicated.
- Models format results in different ways (even when instructed to follow a standard). Some reasonable attempts have been made at parsing results before comparing.
- `test_iterations` is set to 5 to get a good balance of results.

Function calling requires the LLM to understand natural language commands and convert them into structured function calls.

For example, the player might say to an NPC : "go and loot some weapons from the nearby chest". The LLM needs to turn this into the 'npc_loot_items' call, and identify that the player specifically wants 'weapons'. In this case, the expected_response would be: `"<tool_call>{'name': 'npc_loot_items', 'arguments': {'item_mode': 'weapons'}}</tool_call>"`

This use case typically requires LLMs that have been trained to do this, and correctly format the result.

## Benchmark Features
- **Support either local (LMStudio) or remote models**
- **Configurable Test Data**: YAML-based configuration
- **Performance Metrics**: Scoring and timing analysis

## Benchmark installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/stevechk/Mantella-Benchmark.git
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
4. **Configure tests in yaml**:
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
3. **Configure tests in yaml**:
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
python benchmark.py tests/function_test_data.yaml
```

The benchmark will:
1. Load each configured model
2. Run test cases multiple times (configurable in yaml via `test_iterations`)
3. Score the responses, and output results to `results.csv`
4. Dump any failures to `responses.txt` for further investigation

### Test Data Configuration

The test configuration yaml file contains:

- **Test Suites**: A number of test suites, each of which contains test configuration
- **Test Configuration**: Each test defines the setup prompts, test cases (input/expected response), and which scorer to use
- **Model Configuration**: Which models to test and how to connect to them

### Example Test Case

```yaml
test_suites:
  - "function_calling":
      tests:
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

- Built for the Mantella gaming AI project (https://art-from-the-machine.github.io/Mantella), specifically function calling by [yetAnotherModder](https://github.com/yetAnotherModder)
- Uses LM Studio for local model inference (https://lmstudio.ai/)
- Integrates with OpenRouter for remote model access (https://openrouter.ai/)