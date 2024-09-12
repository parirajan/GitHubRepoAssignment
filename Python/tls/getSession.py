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
        self.verify_tls = self.config.get("tls_verify", True)  # Default is True (verify enabled)
        self.cert = (self.config["cert"]["cert_path"], self.config["cert"]["key_path"]) if not self.verify_tls else None

    def sso_login(self):
        """Perform SSO login and obtain CSRF token."""
        login_data = json.dumps({"request": "trySsoLogin"})
        url = f'{self.config["base_url"]}:{self.config["port"]}{self.config["endpoints"]["tryssologin"]}'
        
        # Convert "x-fn-oidc-info" to JSON string as required in headers
        oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
        
        headers = {
            "Content-Type": self.config["headers"]["Content-Type"],
            "x-fn-oidc-info": oidc_info
        }
        
        # Perform the POST request for SSO login, skip TLS if tls_verify is false
        response = self.session.post(url, data=login_data, headers=headers, verify=self.verify_tls, cert=self.cert)
        response_json = response.json()
        self.csrf_token = response_json.get("csrfToken")
        self.download_token = response_json.get("downloadToken")
        logging.info(f"Login successful, CSRF Token: {self.csrf_token}")
        return self.session, self.csrf_token, self.download_token
