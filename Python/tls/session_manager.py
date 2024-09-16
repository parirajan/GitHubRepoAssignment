import requests
from utils import load_config, setup_logger, get_tls_options

def create_session():
    config = load_config()
    logger = setup_logger()
    headers = config['ssoLogin']['headers']
    headers['x-fn-oidc-info'] = json.dumps(headers['x-fn-oidc-info'])

    session = requests.Session()
    tls_options = get_tls_options(config)
    
    login_url = f"{config['target']['protocol']}://{config['target']['ip']}:{config['target']['api_port']}"
    login_url += f"?{{'request':'{config['request_type']}'}}"

    login_response = session.post(login_url, headers=headers, json={'request': 'trySsoLogin'}, **tls_options)
    
    if login_response.status_code == 200:
        logger.info("Successfully logged in")
        tokens = login_response.json()
        headers['downloadToken'] = tokens.get('downloadToken')
        headers['csrfToken'] = tokens.get('csrfToken')
        return session, headers
    else:
        logger.error("Failed to log in")
        return None, None

if __name__ == "__main__":
    session, headers = create_session()
    if session:
        print("Session created with headers:", headers)
    else:
        print("Failed to create session")
