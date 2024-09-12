import utils

def main():
    # Load the configuration
    config = utils.load_config("config.json")
    
    # Initialize the API utility class
    api_utils = utils.APIUtils(config)
    
    # Perform SSO login
    api_utils.sso_login()
    
    # Fetch cluster status for a specific UID
    uid = 123  # Example UID
    cluster_status = api_utils.get_cluster_status(uid)
    print(cluster_status)

if __name__ == "__main__":
    main()
