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

    # Get TLS options
    tls_options = Utils.get_tls_options(config)

    # Perform trySsoLogin (Session Management)
    session_url = Utils.get_full_url(config, "session", "trySsoLogin")
    request_type = Utils.get_request_type(config, "session", "trySsoLogin")
    login_data = "{\"request\":\"trySsoLogin\"}"

    # Log the request details
    logger.info(f"Sending {request_type} request to {session_url}")

    # Make the trySsoLogin request (POST request)
    if request_type == "POST":
        loginResponseObject = s.post(session_url, data=login_data, headers=headers, **tls_options)
    elif request_type == "GET":
        loginResponseObject = s.get(session_url, headers=headers, **tls_options)

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
