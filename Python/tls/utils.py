import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

class APIUtils:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.csrf_token = None
        self.download_token = None
    
    def sso_login(self):
        """Perform SSO login and obtain CSRF token."""
        if self.config["oidc_login"]:
            login_data = json.dumps({"request": "trySsoLogin"})
            url = f'{self.config["base_url"]}{self.config["endpoints"]["tryssologin"]}'
            
            # Convert "x-fn-oidc-info" to JSON string as required in headers
            oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
            
            headers = {
                "AuthToken": self.config["headers"]["AuthToken"],
                "Content-Type": self.config["headers"]["Content-Type"],
                "x-fn-oidc-info": oidc_info
            }
            
            response = self.session.post(url, data=login_data, headers=headers, verify=False)
            response_json = response.json()
            self.csrf_token = response_json.get("csrfToken")
            self.download_token = response_json.get("downloadToken")
            logging.info(f"Login successful, CSRF Token: {self.csrf_token}")
        else:
            # Future implementation for non-OIDC login
            pass
    
    def get_headers(self):
        """Create headers with tokens for further API requests."""
        # Convert "x-fn-oidc-info" to JSON string as required in headers
        oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
        
        headers = {
            "downloadToken": self.download_token,
            "csrfToken": self.csrf_token,
            "x-fn-oidc-info": oidc_info
        }
        return headers
    
    def get_cluster_status(self, uid):
        """Get the cluster health status."""
        url = f'{self.config["base_url"]}{self.config["endpoints"]["get_instances"]}?uid={uid}'
        headers = self.get_headers()
        response = self.session.get(url, headers=headers, verify=False)
        return response.json()

# Load config.json
def load_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
    return config
