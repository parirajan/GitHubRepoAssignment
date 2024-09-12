import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

class GetSession:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()  # Initialize session here
        self.csrf_token = None
        self.download_token = None
        
        # Handle TLS verification and certificate loading
        self.verify_tls = self.config.get("tls_verify", True)
        self.cert = (self.config["cert"]["cert_path"], self.config["cert"]["key_path"]) if not self.verify_tls else None

    def try_sso_login(self):
        """Perform the initial SSO login to get a request session."""
        login_data = {
            "request": "trySsoLogin"
        }
        
        url = f'{self.config["base_url"]}:{self.config["port"]}{self.config["endpoints"]["tryssologin"]}'
        
        # Prepare headers (without tokens initially)
        oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
        headers = {
            "Content-Type": self.config["headers"]["Content-Type"],
            "x-fn-oidc-info": oidc_info
        }

        # Log the request details for debugging
        logging.info("Sending initial SSO login request to URL: %s", url)
        
        # Perform the initial SSO login request
        response = self.session.post(url, json=login_data, headers=headers, verify=self.verify_tls, cert=self.cert)
        
        # Log the full response for debugging
        logging.info("SSO login response status: %s", response.status_code)
        logging.info("SSO login response text: %s", response.text)

        # Check if the response is successful
        if response.status_code != 200:
            logging.error("Failed to establish session. Check the request and try again.")
            return None, None

        # At this point, the session object holds any session-related cookies
        return self.session  # Return the session for the next step
    
    def post_request_with_login_data(self, session):
        """Use the session from trySsoLogin to make a second POST request with login data."""
        post_data = {
            "request": "postRequest",
            "login_data": {}  # Replace with the actual login data
        }
        
        url = f'{self.config["base_url"]}:{self.config["port"]}{self.config["endpoints"]["postRequest"]}'
        
        # Reuse headers, modify if needed (no csrfToken yet, as this is before CSRF token is needed)
        oidc_info = json.dumps(self.config["headers"]["x-fn-oidc-info"])
        headers = {
            "Content-Type": self.config["headers"]["Content-Type"],
            "x-fn-oidc-info": oidc_info
        }

        # Log the request details for debugging
        logging.info("Sending POST request with login data to URL: %s", url)
        logging.info("POST data: %s", post_data)
        
        # Perform the second POST request using the same session
        response = session.post(url, json=post_data, headers=headers, verify=self.verify_tls, cert=self.cert)
        
        # Log the response
        logging.info("POST request response status: %s", response.status_code)
        logging.info("POST request response text: %s", response.text)

        # Check if the response is successful
        if response.status_code != 200:
            logging.error("POST request failed. Check the request and try again.")
            return None

        return response

    def get_session(self):
        """Main function to handle the overall login flow."""
        # First, try SSO login to establish a session
        session = self.try_sso_login()
        if session is None:
            logging.error("SSO login failed. Cannot proceed.")
            return None

        # After establishing a session, perform the second request with login data
        response = self.post_request_with_login_data(session)
        if response is None:
            logging.error("POST request with login data failed.")
            return None

        return session  # Return the session for any future requests
