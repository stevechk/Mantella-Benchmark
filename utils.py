import re
import string
import time
from functools import wraps
from contextlib import contextmanager


def remove_extra_whitespace(text):
    """Remove extra whitespace from text, replacing multiple spaces with single space."""
    return re.sub('\\s+', ' ', text).strip()


def clean_text(text: str) -> str:
    """
    Clean text by removing punctuation, normalizing whitespace, and converting to lowercase.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with punctuation removed, normalized whitespace, and lowercase
    """
    # Remove all punctuation from the sentence
    text_cleaned = text.translate(str.maketrans('', '', string.punctuation))
    # Remove any extra whitespace
    text_cleaned = remove_extra_whitespace(text_cleaned)
    text_cleaned = text_cleaned.lower()

    return text_cleaned

@contextmanager
def Timer(description="Code block"):
    """
    Context manager for timing code blocks.
    
    Args:
        description: Description of the code block being timed
        
    Yields:
        None
        
    Returns:
        float: The elapsed time in seconds
        
    Example:
        with Timer("Model inference") as timer:
            # code to be timed
            pass
        elapsed_time = timer.elapsed_time
    """
    start_time = time.time()
    timer_obj = type('TimerResult', (), {'elapsed_time': 0})()
    yield timer_obj
    end_time = time.time()
    elapsed_time = end_time - start_time
    timer_obj.elapsed_time = elapsed_time
    print(f"{description} took {elapsed_time:.2f} seconds to execute")
    return elapsed_time 