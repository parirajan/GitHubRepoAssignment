import getsession
import json
import utils

def main():
    # Load configuration
    with open('config.json') as f:
        config = json.load(f)

    # Initialize GetSession class with the configuration
    auth_session = getsession.GetSession(config)

    # Call get_session() to perform the login flow
    session = auth_session.get_session()

    if session:
        print("Session established successfully.")
    else:
        print("Failed to establish session.")

if __name__ == "__main__":
    main()
