import requests
from typing import Dict, List, Any, Optional
from base_llm_model import BaseLLMModel
import json
import time


class RemoteLLMModel(BaseLLMModel):
    """Remote LLM model implementation that connects to external API endpoints."""
   
    def __init__(self, 
                 api_endpoint: str,
                 api_key: Optional[str] = None,
                 model_name: str = "default",
                 headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30):
        """
        Initialize the remote LLM model.
        
        Args:
            api_endpoint: The API endpoint URL for the remote LLM service
            api_key: Optional API key for authentication
            model_name: Name of the model to use
            headers: Optional additional headers for the API requests
            timeout: Request timeout in seconds
        """
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        
        # Set up default headers
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        if headers:
            self.headers.update(headers)

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def call(self, prompt: str) -> str:
        """
        Generate a response for a single prompt.
        
        Args:
            prompt: The input prompt string
            
        Returns:
            The generated response string
        """
        max_retries = 5
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/v1/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                response_json = response.json()
                return response_json['choices'][0]['message']['content']
                
            except requests.exceptions.HTTPError as e:
                if (e.response.status_code in [400, 429, 502]) and retry_count < max_retries:
                    print(f"Rate limit exceeded ({e.response.status_code}), retrying in 10 seconds... (attempt {retry_count + 1}/{max_retries + 1})")
                    time.sleep(10)
                    retry_count += 1
                    continue
                elif e.response.status_code in [400, 429, 502]:
                    print(f"Rate limit exceeded ({e.response.status_code}) after retry: {e}")
                    raise Exception(f"Rate limit exceeded after retry: {e}")
                else:
                    print(f"HTTP error occurred: {e}")
                    raise Exception(f"HTTP error occurred: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to call remote LLM: {e}")
                raise Exception(f"Failed to call remote LLM: {e}")
            except (KeyError, IndexError) as e:
                print(f"Invalid response format from remote LLM: {e}")
                raise Exception(f"Invalid response format from remote LLM: {e}")
    
    def call_with_messages(self, messages_json: str) -> str:
        """
        Generate a response for a conversation with multiple messages.
        
        Args:
            messages_json: JSON string containing the conversation messages
            
        Returns:
            The generated response string
        """
        max_retries = 5
        retry_count = 0
        
        while retry_count <= max_retries:
            try:            
                payload = {
                    "model": self.model_name,
                    "messages": messages_json
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/v1/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                response_json = response.json()
                return response_json['choices'][0]['message']['content']
                
            except json.JSONDecodeError as e:
                print(f"Invalid JSON format for messages: {e}")
                raise Exception(f"Invalid JSON format for messages: {e}")
            except requests.exceptions.HTTPError as e:
                if (e.response.status_code in [400, 429, 500, 502]):
                    if retry_count < max_retries:
                        print(f"Rate limit exceeded ({e.response.status_code}), retrying in 10 seconds... (attempt {retry_count + 1}/{max_retries + 1})")
                        time.sleep(10)
                        retry_count += 1
                        continue
                    else:
                        print(f"Rate limit exceeded ({e.response.status_code}) after retry: {e}")
                        raise Exception(f"Rate limit exceeded after retry: {e}")
                else:
                    print(f"HTTP error occurred: {e}")
                    raise Exception(f"HTTP error occurred: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to call remote LLM: {e}")
                raise Exception(f"Failed to call remote LLM: {e}")
            except (KeyError, IndexError) as e:
                print(f"Invalid response format from remote LLM: {e}")
                raise Exception(f"Invalid response format from remote LLM: {e}")
    
    def set_api_key(self, api_key: str) -> None:
        """Update the API key for authentication."""
        self.api_key = api_key
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        elif "Authorization" in self.headers:
            del self.headers["Authorization"]
    
    def set_model_name(self, model_name: str) -> None:
        """Update the model name to use for requests."""
        self.model_name = model_name
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the remote model."""
        return {
            "type": "remote",
            "api_endpoint": self.api_endpoint,
            "model_name": self.model_name,
            "has_api_key": bool(self.api_key),
            "timeout": self.timeout
        } 