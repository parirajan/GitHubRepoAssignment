import json
import logging

# Define the ConfigLoader class
class ConfigLoader:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = json.load(file)

    @property
    def ssologin(self):
        return self.config.get('ssologin', {})

    @property
    def tlsConfig(self):
        return self.config.get('validateTls', {})

# Initialize the config globally
config = ConfigLoader('path_to_config_file.json')

# Define the LoggingHandler class
class LoggingHandler:
    @staticmethod
    def getExecutionLogger(name):
        # Create or get the logger for the given name
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)  # Set logging level

        # Check if logger already has handlers (to avoid adding them multiple times)
        if not logger.handlers:
            # Create console and file handlers
            console_handler = logging.StreamHandler()
            file_handler = logging.FileHandler(f'{name}.log')

            # Set handler levels
            console_handler.setLevel(logging.ERROR)
            file_handler.setLevel(logging.ERROR)

            # Create formatter and add it to handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            # Add handlers to the logger
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        return logger

# Create a logger object by referring to LoggingHandler (which is what you expect to use in getSession.py)
logger = LoggingHandler
