import requests
from utils import Utils
from login_session import create_login_session

def get_session(config):
    logger = Utils.setup_logger()

    # Create the login session and get tokens
    session_data = create_login_session(config)
    if not session_data:
        logger.error("Failed to create login session.")
        return None

    # Extract tokens from the login response
    download_token = session_data.get("downloadToken")
    csrf_token = session_data.get("csrfToken")
    
    if not download_token or not csrf_token:
        logger.error("Download token or CSRF token not found in login response.")
        return None

    # Prepare the session headers with loginname
    session_headers = {
        "downloadToken": download_token,
        "csrfToken": csrf_token,
        "loginname": json.dumps(config["ssoLogin"]["headers"]["loginname"])  # Reuse loginname from config
    }

    logger.info(f"Session established with headers: {session_headers}")
    print(f"Session Headers: {session_headers}")
    
    return session_headers
