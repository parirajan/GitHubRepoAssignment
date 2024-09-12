import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

class GetSession:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.csrf_token = None
        self.download_token = None
        
        # Handle TLS verification and certificate loading
        self.verify_tls = self.config.get("tls_verify", True)
        self.cert = (self.config["cert"]["cert_path"], self.config["cert"]["key_path"]) if not self.verify_tls else None

    def sso_login(self):
        """Perform SSO login and obtain CSRF token."""
        # The correct data format to send to the server
        login_data = {
            "request": "trySsoLogin",  # Make sure this matches the API's expected request format
            "data": {}  # Add any additional required data for the login if necessary
        }
        
        url = f'{self.config["base_url"]}:{self.config["port"]}{self.config["endpoints"]["tryssologin"]}'
        
        # Convert "x-fn-oidc-info" to JSON string as required in headers
        oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
        
        headers = {
            "Content-Type": self.config["headers"]["Content-Type"],
            "x-fn-oidc-info": oidc_info
        }
        
        # Log the request details for debugging
        logging.info("Sending POST request to URL: %s", url)
        logging.info("Login data: %s", login_data)
        logging.info("Headers: %s", headers)
        
        # Perform the POST request for SSO login
        response = self.session.post(url, json=login_data, headers=headers, verify=self.verify_tls, cert=self.cert)
        
        # Log the full response for debugging
        logging.info("Login response status: %s", response.status_code)
        logging.info("Login response text: %s", response.text)

        # Attempt to parse the JSON response
        try:
            response_json = response.json()
            logging.info("Parsed JSON: %s", response_json)
        except json.JSONDecodeError as e:
            logging.error("Failed to parse response as JSON: %s", e)
            return None, None, None
        
        # Extract tokens (if available)
        self.csrf_token = response_json.get("csrfToken")
        self.download_token = response_json.get("downloadToken")
        
        # Log the tokens to verify if they're being extracted correctly
        logging.info("CSRF Token: %s", self.csrf_token)
        logging.info("Download Token: %s", self.download_token)
        
        return self.session, self.csrf_token, self.download_token
    
    def basic_auth_login(self):
        """Perform basic auth login (for future implementation)."""
        pass

    def get_session(self):
        """Determine which authentication method to use."""
        if self.config.get("oidc_login", False):
            return self.sso_login()
        else:
            return self.basic_auth_login()
