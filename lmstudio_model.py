import subprocess
from typing import Dict, List, Any, Optional

import requests

from base_llm_model import BaseLLMModel

#lm studio wrapper - required because lm studio python API is not compatible with the older versions of python that work with tensorflow
# use model_path to load the model, as this avoids LM Studio getting confused if there are multiple versions of the model e.g. different quants
class LmStudioModel(BaseLLMModel):

    def __init__(self, 
                 api_endpoint: str,
                 model_path: str = "default",
                 context_length: int = 8192):
        """
        Initialize the LM Studio model.
        
        Args:
            api_endpoint: The API endpoint URL for the LM Studio service
            api_key: Optional API key for authentication
            model_path: Path/name of the model to use
            context_length: Context length for the model
            headers: Optional additional headers for the API requests
            timeout: Request timeout in seconds
        """
        
        # Set LM Studio specific attributes
        self.api_endpoint = api_endpoint
        self.model_path = model_path
        self.context_length = context_length

    def _list_loaded_models(self):
        process = subprocess.Popen(["lms", "ps"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 universal_newlines=True,
                                 encoding='utf-8',
                                 errors='replace',
                                 bufsize=1024*1024)  # 1MB buffer
        try:
            output, error = process.communicate(timeout=10)
        except subprocess.TimeoutExpired as e:
            process.kill()
            raise Exception(f"`lms ps` Process timed out {e.output} / {e.stderr}")
        
        if process.returncode != 0:
            print(f"Failed to check model status: {error}")
            raise Exception(f"Failed to check model status: {error}")
        return output

    def _list_available_models(self):
        process = subprocess.Popen(["lms", "ls", "--json"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, 
                                 universal_newlines=True,
                                 encoding='utf-8',
                                 errors='replace',
                                 bufsize=1024*1024)  # 1MB buffer
        try:
            output, error = process.communicate(timeout=10)
        except subprocess.TimeoutExpired as e:
            process.kill()
            raise Exception(f"`lms ls` Process timed out {e.output} / {e.stderr}")
        
        if process.returncode != 0:
            print(f"Failed to check model status: {error}")
            raise Exception(f"Failed to check model status: {error}")
        return output


    def _get_model_name(self) -> bool:
        output = self._list_loaded_models()

        #check if either the path or name is in the output
        if not (self.model_path in output):
            raise Exception(f"Model {self.model_path} is not loaded")
        
        #grep the output to find the model name
        # Find the model identifier by matching the path in the output
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if self.model_path in line:
                # The identifier is typically on the line starting with "Identifier:"
                # Look at previous lines to find it
                for j in range(i-3, i+1):
                    if j >= 0 and lines[j].strip().startswith("Identifier:"):
                        self.model_name = lines[j].split(":", 1)[1].strip()
                        return self.model_name
                        
        raise Exception(f"Could not find identifier for model path {self.model_path} in output")


    def load(self):

        if self.model_path in self._list_loaded_models():
            print(f"Model {self.model_path} is already loaded")
            return
        
        if self.model_path not in self._list_available_models():
            print(f"Model {self.model_path} is not available - download it first")
            raise Exception(f"Model {self.model_path} is not available")

        #load the model into lm studio
        print(f"Loading model {self.model_path} with context length {self.context_length}")
        process = subprocess.Popen(["lms", "load", self.model_path, "--context-length", str(self.context_length)], 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 encoding='utf-8',
                                 errors='replace',
                                 bufsize=1024*1024)  # 1MB buffer
        
        # Read output and wait for process to complete
        try:
            output, error = process.communicate(timeout=60)
        except subprocess.TimeoutExpired as e:
            process.kill()
            print(f"Failed to load model {self.model_path}: {e.output} / {e.stderr}")
            raise Exception(f"Load model timed out {e.output} / {e.stderr}")
        
        #get return code
        return_code = process.returncode
        if return_code != 0:
            print(f"Failed to load model {self.model_path}")
            print(f"Error: {error}")
            raise Exception(f"Failed to load model {self.model_path}")
        

    def unload(self):
        #check if model is not already loaded
        #grep output for the model name
        if not self.model_path in self._list_loaded_models():
            print(f"Model {self.model_path} is not loaded")
            return

        model_name = self._get_model_name()

        #unload the model from lm studio
        process = subprocess.Popen(["lms", "unload", self.model_name], 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 bufsize=1024*1024)  # 1MB buffer
        try:
            output, error = process.communicate(timeout=60)  # 1 minute timeout
        except subprocess.TimeoutExpired as e:
            process.kill()
            raise Exception(f"Process timed out after 1 minute: {e.output} / {e.stderr}")

        #get return code
        if process.returncode != 0:
            print(f"Failed to unload model {self.model_name}")
            print(f"Error: {error}")
            raise Exception(f"Failed to unload model {self.model_name}")

    def call(self, prompt: str) -> str:
        #call the model using the openapi endpoint
        response = requests.post(
            f"{self.api_endpoint}/v1/chat/completions",
            timeout=30,
            json={
                "model": self.model_path,
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        # Parse the JSON response and extract the message content
        response_json = response.json()
        response_text = response_json['choices'][0]['message']['content']
        return response_text


    def call_with_messages(self, messages_json: str) -> str:
        #call the model using the openapi endpoint
        response = requests.post(
            f"{self.api_endpoint}/v1/chat/completions",
            timeout=30,
            json={
                "model": self.model_path,
                "messages": messages_json
            }
        )

        # Parse the JSON response and extract the message content
        response_json = response.json()

        if not 'choices' in response_json:
            print(f"No choices in response: {response_json}")
            raise Exception(f"No choices in response: {response_json}")

        response_text = response_json['choices'][0]['message']['content']
        return response_text
