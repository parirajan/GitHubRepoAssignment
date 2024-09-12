import json
import utils
import getsession

def main():
    # Load the configuration
    with open("config.json") as f:
        config = json.load(f)
    
    # Initialize the GetSession class for authentication
    auth_session = getsession.GetSession(config)
    
    # Obtain session, csrf_token, and download_token from the chosen auth method
    session, csrf_token, download_token = auth_session.get_session()  # Ensure this method is called properly
    
    # Initialize the API utility class with session and tokens
    api_utils = utils.APIUtils(session, csrf_token, download_token, config)
    
    # Fetch cluster status
    cluster_status = api_utils.get_cluster_status()
    print(json.dumps(cluster_status, indent=4))

if __name__ == "__main__":
    main()
