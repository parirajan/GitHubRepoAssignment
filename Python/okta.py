from authlib.integrations.requests_client import OAuth2Session
import webbrowser

# Okta configuration
OKTA_DOMAIN = 'your-okta-domain.okta.com'
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:8080/callback'

# OIDC endpoints
AUTHORIZATION_ENDPOINT = f'https://{OKTA_DOMAIN}/oauth2/default/v1/authorize'
TOKEN_ENDPOINT = f'https://{OKTA_DOMAIN}/oauth2/default/v1/token'
USERINFO_ENDPOINT = f'https://{OKTA_DOMAIN}/oauth2/default/v1/userinfo'

# Initialize OAuth2Session
session = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI)

# Step 1: Generate authorization URL
def get_authorization_url():
    uri, state = session.create_authorization_url(AUTHORIZATION_ENDPOINT, scope='openid profile email')
    return uri

# Step 2: Handle the callback and exchange the authorization code for tokens
def fetch_tokens(authorization_response_url):
    token = session.fetch_token(TOKEN_ENDPOINT, authorization_response=authorization_response_url, client_secret=CLIENT_SECRET)
    return token

# Step 3: Get user info from Okta
def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(USERINFO_ENDPOINT, headers=headers)
    return response.json()

if __name__ == '__main__':
    # Step 1: Redirect the user to the Okta login page (OIDC Authorization URL)
    authorization_url = get_authorization_url()
    print(f"Visit this URL to log in: {authorization_url}")
    webbrowser.open(authorization_url)

    # Step 2: After login, Okta will redirect back with the authorization code
    redirect_response = input("Paste the full redirect URL here: ")

    # Step 3: Exchange the authorization code for tokens
    tokens = fetch_tokens(redirect_response)
    print(f"Access Token: {tokens['access_token']}")

    # Step 4: Use the access token to get user info
    user_info = get_user_info(tokens['access_token'])
    print(f"User Info: {user_info}")
