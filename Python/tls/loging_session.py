import requests
import json
from utils import Utils

def create_login_session(config):
    logger = Utils.setup_logger()

    # Check if SSO login is enabled
    sso_config = config.get("ssoLogin", {})
    if not sso_config.get("enabled", False):
        logger.error("SSO Login is disabled.")
        return None

    # Get TLS options
    tls_options = Utils.get_tls_options(config)

    # Prepare headers
    headers = sso_config.get("headers", {})
    headers["x-fn-oidc-info"] = json.dumps({"loginname":"user"})

    # Prepare the data as a JSON object
    login_data = json.dumps({"request": "trySsoLogin"})

    # Construct the URL with the request query
    login_url = Utils.get_target_url(config) + '?{"request":"postRequest"}'
    
    # Log the request details
    logger.info(f"Sending POST request to {login_url} with headers: {headers} and data: {login_data}")

    # Create a session object
    session = requests.Session()

    # Make the POST request using session object, with headers, data, and TLS options
    response = session.post(login_url, data=login_data, headers=headers, verify=tls_options["verify"], cert=tls_options.get("cert"))

    # Log and print the response
    logger.info(f"Login Response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        logger.error("Login failed.")
        return None

    response_data = response.json()
    return response_data

