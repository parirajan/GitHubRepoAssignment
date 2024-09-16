import json
import logging

def load_config(path='config.json'):
    with open(path, 'r') as file:
        return json.load(file)

def setup_logger():
    logger = logging.getLogger('SaferPaymentsLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def prepare_url(config):
    base_url = f"{config['target']['protocol']}://{config['target']['ip']}:{config['target']['api_port']}"
    request_type = config.get('request_type', 'postRequest')
    return f"{base_url}/?{{\"request\":\"{request_type}\"}}"
