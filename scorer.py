from abc import ABC, abstractmethod
from typing import Any, Dict, List

class Scorer(ABC):
    """Abstract base class for model response scorers."""
    
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def score(self, system_prompt: str, model_name: str, test_name: str, questions: List[List[Dict[str, Any]]], references: List[str], candidates: List[str]) -> List[float]:
        pass
    
    @abstractmethod
    def shutdown(self):
        pass

