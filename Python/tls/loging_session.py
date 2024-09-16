import requests
import json
from urllib.parse import quote

def create_login_session(config):
    # Sample configuration and logger setup
    logger = config.get('logger', print)

    # Define the headers and data payload
    headers = {
        "Content-Type": "application/json",
        "x-fn-oidc-info": json.dumps({"loginname": "user"})
    }
    login_data = json.dumps({"request": "trySsoLogin"})

    # URL and Query formatting
    request_type = {"request": "postRequest"}
    json_request = json.dumps(request_type)
    encoded_request = quote(json_request)  # URL-encode the JSON string

    # Full URL with query
    login_url = f"https://example.com/api/?{encoded_request}"

    # Create a session and send the request
    session = requests.Session()
    response = session.post(login_url, data=login_data, headers=headers, verify=False)

    # Log the response
    logger(f"Login Response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        logger("Login failed.")
        return None

    return response.json()

# Example usage (assuming 'logger' and other necessary configurations are set)
config = {
    'logger': print  # Using print function for logging in this example
}
create_login_session(config)
