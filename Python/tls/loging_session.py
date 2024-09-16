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
    headers["loginname"] = json.dumps(headers.get("loginname", {}))  # Ensure loginname is passed as a JSON string
    login_data = json.dumps({
        "request": "trySsoLogin"
    })

    # Fetch the request type from config
    request_type = sso_config.get("request_type", "PostRequest")
    
    # Construct URL with dynamic request type and colon at the end
    login_url = Utils.get_target_url(config, f'/?{{"request":"{request_type}:"}}')  # URL with dynamic request_type and colon
    
    # Log the fully-formed POST request details before sending
    logger.info(f"POST Request URL: {login_url}")
    logger.info(f"POST Request Headers: {headers}")
    logger.info(f"POST Request Data: {login_data}")
    logger.info(f"POST Request Verify: {tls_options['verify']}")
    print(f"POST Request URL: {login_url}")
    print(f"POST Request Headers: {headers}")
    print(f"POST Request Data: {login_data}")
    print(f"POST Request Verify: {tls_options['verify']}")

    # Create a session object
    session = requests.Session()

    # Make the POST request using session object, with headers, data, and TLS options
    response = session.post(login_url, data=login_data, headers=headers, verify=tls_options["verify"], cert=tls_options.get("cert"))

    # Log and print the response
    logger.info(f"Login Response: {response.status_code} - {response.text}")
    print(f"Login Response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        logger.error("Login failed.")
        return None

    response_data = response.json()
    return response_data  # Assuming response contains tokens
