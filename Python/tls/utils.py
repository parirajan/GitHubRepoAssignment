import json
import logging

def load_config(path='config.json'):
    """Load and return the JSON configuration."""
    with open(path, 'r') as file:
        return json.load(file)

def setup_logger():
    """Configure and return a logger."""
    logger = logging.getLogger('SaferPaymentsLogger')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_tls_options(config):
    """Return TLS options from the config if TLS is enabled."""
    tls = config.get('tls_validation', {})
    if tls.get('enabled', False):
        return {
            'verify': tls.get('verify', False),
            'cert': (tls.get('clientCert'), tls.get('clientKey'))
        }
    return {'verify': False}
