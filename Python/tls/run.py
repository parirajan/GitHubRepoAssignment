import requests
from getSession import getSession
from utils import config, construct_url

# Example user credentials for non-SSO login
USERNAME = "your_username"
PASSWORD = "your_password"

def trySsoLogin(session, url):
    try:
        # Make a simulated request to check SSO login
        response = session.get(f'{url}sso_login_check')

        if response.status_code == 200:
            print("SSO login successful:", response.json())
        else:
            print(f"SSO login failed with status code {response.status_code}")

    except Exception as e:
        print(f"SSO login encountered an error: {str(e)}")


def tryUserPassLogin(session, url, username, password):
    try:
        # Make a simulated request with basic auth using username and password
        response = session.get(f'{url}login', auth=(username, password))

        if response.status_code == 200:
            print("User/Pass login successful:", response.json())
        else:
            print(f"User/Pass login failed with status code {response.status_code}")

    except Exception as e:
        print(f"User/Pass login encountered an error: {str(e)}")


def main():
    # Create a session object
    session = requests.Session()

    # Call getSession to configure the session (SSO and TLS)
    configured_session = getSession(session)

    # Verify session configuration
    if configured_session:
        print("Session Headers:", configured_session.headers)
        print("Session Verify:", configured_session.verify)
        if configured_session.cert:
            print("Session Certificates:", configured_session.cert)

        # Construct the base URL from the config (without `/api`)
        url = construct_url()
        print("Constructed URL:", url)
        
        # Check if SSO is enabled in the config
        ssologin = config.ssologin
        ssoEnabled = ssologin.get("enabled", False)

        if ssoEnabled:
            print("SSO login is enabled. Trying SSO login...")
            trySsoLogin(configured_session, url)
        else:
            print("SSO login is not enabled. Using username/password for login...")
            tryUserPassLogin(configured_session, url, USERNAME, PASSWORD)
    
    else:
        print("Failed to configure session.")


if __name__ == "__main__":
    main()
