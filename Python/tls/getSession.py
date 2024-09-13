import requests
import json
from utils import Utils, Logger

def get_session(config):
    # Setup logging
    logger = Logger.setup_logger()

    # Create headers from the config (directly use tokenname as a JSON object)
    headers = {
        "tokenname": json.dumps(config["headers"]["tokenname"]),
        "Content-Type": config["headers"]["Content-Type"]
    }

    # Initialize session
    s = requests.session()

    # Get TLS options (verify and cert handling)
    tls_options = Utils.get_tls_options(config)

    # Prepare the data payload for the login request, including the login_type
    login_data = json.dumps({
        "request": config["login_type"]
    })

    # Build URL with request as a query string
    session_url = Utils.get_full_url(config, "session", "postRequest") + '?{"request":"postRequest"}'
    
    logger.info(f"Sending POST request to {session_url} with login_type: {config['login_type']}")

    # Make the postRequest (POST request)
    loginResponseObject = s.post(session_url, data=login_data, headers=headers, verify=tls_options["verify"], cert=tls_options.get("cert"))

    loginResponse = loginResponseObject.text
    logger.info("Login Response: %s", loginResponse)

    # Parse login response and extract tokens
    loginResponseJson = json.loads(loginResponse)
    downloadToken = loginResponseJson["downloadToken"]
    csrfToken = loginResponseJson["csrfToken"]

    # Prepare login payload for subsequent requests
    loginpayload = {
        'downloadToken': downloadToken,
        'csrfToken': csrfToken,
        'tokenname': config["headers"]["tokenname"]  # Directly use the tokenname JSON object here
    }

    logger.info("Login Payload: %s", loginpayload)

    # Return session and loginpayload
    return s, loginpayload
