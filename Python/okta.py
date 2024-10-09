import requests

# Okta organization URL and API endpoint
OKTA_DOMAIN = 'https://your-okta-domain.okta.com'
AUTHN_URL = f'{OKTA_DOMAIN}/api/v1/authn'

# User credentials
USERNAME = 'your_username'
PASSWORD = 'your_password'

# Step 1: Authenticate the user using the Authentication API
def authenticate_user(username, password):
    payload = {
        'username': username,
        'password': password,
        'options': {
            'multiOptionalFactorEnroll': False,
            'warnBeforePasswordExpired': False
        }
    }

    # Make the request to the Okta Authentication API
    response = requests.post(AUTHN_URL, json=payload)
    
    if response.status_code == 200:
        auth_data = response.json()
        print(f"Authentication successful for {username}")
        session_token = auth_data['sessionToken']  # You'll get the session token
        return session_token
    else:
        print(f"Authentication failed: {response.status_code} {response.text}")
        return None

# Step 2: Use session token in the Authorization Code or OIDC flow to create a session
def redirect_to_oidc(session_token):
    # OIDC Authorization URL
    AUTHORIZATION_URL = f'{OKTA_DOMAIN}/oauth2/default/v1/authorize'

    # Parameters for the authorization request
    params = {
        'client_id': 'your_client_id',
        'response_type': 'code',
        'scope': 'openid profile email',
        'redirect_uri': 'http://localhost:8080/callback',
        'state': 'random_state_string',
        'sessionToken': session_token
    }

    # Redirect the user to the OIDC authorization URL with the session token
    response = requests.get(AUTHORIZATION_URL, params=params)
    print(f"Redirecting to OIDC: {response.url}")
    return response.url

if __name__ == "__main__":
    # Step 1: Authenticate user with username and password
    session_token = authenticate_user(USERNAME, PASSWORD)

    if session_token:
        # Step 2: Redirect to OIDC flow with the session token
        oidc_url = redirect_to_oidc(session_token)
        print(f"Visit this URL to continue OIDC authentication: {oidc_url}")
