import okta
from okta.client import Client as OktaClient
import asyncio

# Configuration for Okta
config = {
    'orgUrl': 'https://your-okta-domain.okta.com',  # Replace with your Okta domain
    'token': 'your_api_token'  # API token from Okta Admin Console
}

# Initialize Okta Client
okta_client = OktaClient(config)

# Step 1: Authenticate User
async def authenticate_user(username, password):
    try:
        # Call the Authentication API to verify the user credentials
        authentication_response = await okta_client.authenticate(
            username=username,
            password=password
        )
        
        # Check if authentication was successful
        if authentication_response.authentication_status == "SUCCESS":
            print(f"Authentication successful for {username}")
            session_token = authentication_response.session_token
            return session_token
        
        else:
            print(f"Authentication failed: {authentication_response.error}")
            return None

    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return None

# Step 2: Exchange Session Token for a Session or Token
async def create_session_from_token(session_token):
    try:
        # Create a new session based on the session token
        session = await okta_client.create_session(session_token=session_token)
        
        if session:
            print(f"Session created. Session ID: {session.id}")
            return session.id
        
        else:
            print("Failed to create session.")
            return None

    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return None

# Step 3: Logout from Okta Session
async def logout_user(session_id):
    try:
        # Terminate the session to log the user out
        await okta_client.close_session(session_id)
        print(f"Session {session_id} terminated. User logged out.")
    
    except Exception as e:
        print(f"Error during logout: {str(e)}")

# Main function
async def main():
    username = 'your_username'  # Okta username
    password = 'your_password'  # Okta password

    # Authenticate user and get session token
    session_token = await authenticate_user(username, password)

    if session_token:
        # Create session with the session token
        session_id = await create_session_from_token(session_token)

        if session_id:
            # Perform further tasks with the authenticated session...

            # Logout the user when done
            await logout_user(session_id)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
