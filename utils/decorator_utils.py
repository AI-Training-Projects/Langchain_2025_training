"""Decorator examples for tracking Langchain examples"""

import time
import functools

def timer_decorator(func):
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Function '{func.__name__}' took {run_time:.4f} seconds to execute")
        return result
    return wrapper

##############  function_logger   ##################
import logging
from datetime import datetime
import inspect
import functools
import os


def function_logger(func):
    """Decorator to log function details and execution to a named, time-stamped file.
    
    Creates a log file with format: {function_name}_runlog_{timestamp}.log
    
    Features:
    - Creates unique log files named after the decorated function
    - Includes timestamp in filename for multiple runs
    - Creates a unique logger instance for each function call
    - Uses function-specific name for logger based on timestamp
    - Includes proper handler cleanup
    - Prevents duplicate logging
    - Captures function metadata including:
        * Function name
        * Docstring
        * Arguments
        * Source code
        * Return values or exceptions
    
    Example log filename: 
        search_wikipedia_runlog_20250221_123456.log
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Setup logging with a new FileHandler each time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{func.__name__}_runlog_{timestamp}.log"
        
        # Create a new logger for this function call
        logger = logging.getLogger(f"{func.__name__}_{timestamp}")
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicate logging
        logger.handlers = []
        
        # Create and add new file handler
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Log function details
        logger.info(f"Function Name: {func.__name__}")
        logger.info(f"Docstring: {func.__doc__}")
        logger.info(f"Arguments: args={args}, kwargs={kwargs}")
        
        # Get source code
        source = inspect.getsource(func)
        logger.info(f"Source Code:\n{source}")
        
        # Execute function and log result
        try:
            result = func(*args, **kwargs)
            logger.info(f"Return Value: {result}")
            return result
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            raise
        finally:
            # Clean up - remove handlers
            file_handler.close()
            logger.removeHandler(file_handler)
    
    return wrapper