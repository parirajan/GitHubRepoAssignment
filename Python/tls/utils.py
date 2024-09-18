import json
import logging

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

class LoggingHandler:
    @staticmethod
    def getExecutionLogger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler('file.log')
        c_handler.setLevel(logging.ERROR)
        f_handler.setLevel(logging.ERROR)
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        return logger

# Instantiate the ConfigLoader with the path to the configuration file
config = ConfigLoader('path_to_config_file.json')
