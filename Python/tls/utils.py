import json
import logging
import os
import requests

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


def sso_login(session: requests.Session, config_loader: ConfigLoader, logger):
    """Performs SSO login and returns session with updated headers."""
    try:
        # Get login URL and headers from the configuration
        login_url = config_loader.get_config('endpoints', 'loginUrl')
        target_config = config_loader.get_config('target', {})
        api_url = f"https://{target_config.get('ip')}:{target_config.get('apiPort')}{login_url}"

        # Get required headers from the config
        headers = config_loader.get_config('ssoLogin', 'reqHeaders', {})
        if not isinstance(headers, dict):
            logger.error("SSO login headers are not properly formatted")
            return None

        # Example login data payload
        login_data = {"request": {"trySsoLogin": "Y"}}  # Based on the image you shared

        # Make the SSO login request
        logger.info(f"Attempting SSO login at {api_url}")
        login_response = session.post(api_url, json=login_data, headers=headers, verify=False)
        
        if login_response.status_code != 200:
            logger.error(f"SSO login failed with status code: {login_response.status_code}")
            return None

        # Parse response for tokens and cookies
        logger.info(f"SSO login successful, processing tokens.")
        cookie_header = login_response.headers.get('Set-Cookie')
        if cookie_header:
            # Add the cookie to the session headers
            session.headers.update({"Cookie": cookie_header})

        # Extract tokens from the login response JSON
        login_response_json = login_response.json()
        download_token = login_response_json.get('downloadToken', '')
        csrf_token = login_response_json.get('csrfToken', '')

        # Add tokens to the session headers
        session.headers.update({
            'downloadToken': download_token,
            'csrftoken': csrf_token,
            'x-fn-oidc-info': '{"loginname": "user"}'  # Update with dynamic login if needed
        })

        return session

    except Exception as e:
        logger.error(f"Error during SSO login: {str(e)}")
        return None
