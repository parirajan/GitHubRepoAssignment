import requests
from utils import load_config, setup_logger, prepare_url

def create_session():
    config = load_config()
    logger = setup_logger()
    url = prepare_url(config)
    
    headers = config['ssoLogin']['headers']
    login_data = '{"request":"trySsoLogin"}'  # This can be adapted or extended as needed

    session = requests.Session()
    response = session.post(url, data=login_data, headers=headers, verify=False)

    if response.status_code == 200:
        logger.info("Login successful.")
        return response.json()
    else:
        logger.error(f"Login failed with status: {response.status_code}")
        return None

if __name__ == "__main__":
    session_info = create_session()
    if session_info:
        print("Session info:", session_info)
    else:
        print("Failed to create session.")
