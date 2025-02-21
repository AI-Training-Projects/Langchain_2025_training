# Example usage of both decorators
# With current file in SAME directory as the decorator_utils.py file, use this following import
from decorator_utils import timer_decorator, function_logger

@timer_decorator
@function_logger
def process_data(data_list, multiplier=2):
    """
    Process a list of numbers by multiplying each by a factor.
    
    Args:
        data_list (list): List of numbers to process
        multiplier (int): Factor to multiply by
    
    Returns:
        list: Processed numbers
    """
    return [x * multiplier for x in data_list]

# Test the decorated function
test_data = list(range(100))
result = process_data(test_data, multiplier=33)