import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

class APIUtils:
    def __init__(self, session, csrf_token, download_token, config):
        self.config = config
        self.session = session
        self.csrf_token = csrf_token
        self.download_token = download_token
    
    def build_url(self, endpoint):
        """Construct the full URL with port and endpoint."""
        return f'{self.config["base_url"]}:{self.config["port"]}{endpoint}'
    
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
    
    def get_cluster_status(self):
        """Get the cluster health status using the variable uid."""
        uid = self.config["uid"]
        url = self.build_url(self.config["endpoints"]["get_instances"]) + f'?uid={uid}'
        headers = self.get_headers()
        response = self.session.get(url, headers=headers, verify=self.config["tls_verify"], cert=self.config["cert"])
        return response.json()
