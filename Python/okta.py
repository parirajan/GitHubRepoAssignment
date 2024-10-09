import requests

# Okta organization URL and API endpoint
OKTA_DOMAIN = 'https://your-okta-domain.okta.com'
SESSION_URL = f'{OKTA_DOMAIN}/api/v1/sessions'

# Session token obtained after user authentication
session_token = 'your_session_token'

def validate_session_token(session_token):
    # Request payload to create a session
    data = {
        'sessionToken': session_token
    }
    
    # Make the request to create a session
    response = requests.post(SESSION_URL, json=data)
    
    if response.status_code == 200:
        session_info = response.json()
        print("Session token is valid!")
        print("Session ID:", session_info['id'])
        print("Session Expires At:", session_info['expiresAt'])
        return True
    else:
        print(f"Invalid session token: {response.status_code}, {response.text}")
        return False

if __name__ == "__main__":
    # Validate the session token
    validate_session_token(session_token)
