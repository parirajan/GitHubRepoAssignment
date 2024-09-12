import json
import logging
import os

class ConfigLoader:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        with open(config_path, 'r') as file:
            return json.load(file)

    def get_config(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)


class LoggingHandler:
    def __init__(self, log_file='application.log'):
        self.logger = self._setup_logger(log_file)

    def _setup_logger(self, log_file):
        logger = logging.getLogger('session_logger')
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_execution_logger(self, name):
        return logging.getLogger(name)
