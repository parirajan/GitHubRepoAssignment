import requests
from utils import ConfigLoader, LoggingHandler
from getSession import getSession
import json

def get_cluster_health(session, config_path):
    logger = LoggingHandler().get_execution_logger(__name__)
    try:
        # Get endpoint and API URL from config
        config_loader = ConfigLoader(config_path)
        target_config = config_loader.get_config('target', {})
        cluster_health_url = config_loader.get_config('endpoints', 'clusterHealthUrl')

        api_url = f"https://{target_config.get('ip')}:{target_config.get('apiPort')}{cluster_health_url}"

        # Make API request for Cluster Health Status
        response = session.get(api_url)
        if response.status_code == 200:
            logger.info("Cluster Health Data Retrieved")
            return json.loads(response.text)
        else:
            logger.error(f"Failed to get cluster health status: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error fetching Cluster Health: {str(e)}")
        return None

def get_fli_status(session, config_path):
    logger = LoggingHandler().get_execution_logger(__name__)
    try:
        # Get endpoint and API URL from config
        config_loader = ConfigLoader(config_path)
        target_config = config_loader.get_config('target', {})
        fli_status_url = config_loader.get_config('endpoints', 'fliStatusUrl')

        api_url = f"https://{target_config.get('ip')}:{target_config.get('apiPort')}{fli_status_url}"

        # Make API request for FLI Status
        response = session.get(api_url)
        if response.status_code == 200:
            logger.info("FLI Status Data Retrieved")
            return json.loads(response.text)
        else:
            logger.error(f"Failed to get FLI status: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error fetching FLI Status: {str(e)}")
        return None

if __name__ == "__main__":
    config_path = "path_to_config.json"

    # Initialize session
    session = getSession(requests.Session(), config_path)

    if session:
        # Get Cluster Health and FLI Status
        cluster_health_data = get_cluster_health(session, config_path)
        print(json.dumps(cluster_health_data, indent=4, sort_keys=True))

        fli_status_data = get_fli_status(session, config_path)
        print(json.dumps(fli_status_data, indent=4, sort_keys=True))
