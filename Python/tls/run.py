import requests
from getSession import getSession

# Create a new Session object
session = requests.Session()

# Get the configured session using the getSession function
configured_session = getSession(session)

# Check if the session was successfully configured
if configured_session:
    print("Session Headers:", configured_session.headers)
    print("Session Verify:", configured_session.verify)
    if configured_session.cert:
        print("Session Certificates:", configured_session.cert)
else:
    print("Failed to configure session.")
