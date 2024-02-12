import requests
import logging
import json

# Set up logging
logging.basicConfig(filename='metadata_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Constants for the IMDSv2 endpoint and the token request
TOKEN_URL = "http://169.254.169.254/latest/api/token"
METADATA_URL = "http://169.254.169.254/latest/meta-data/"

def get_token():
    headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    response = requests.put(TOKEN_URL, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logging.error("Failed to retrieve IMDSv2 token")
        return None

def fetch_metadata(url, token, path=''):
    headers = {"X-aws-ec2-metadata-token": token}
    full_url = f"{url}{path}"
    response = requests.get(full_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to fetch metadata for path: {path}")
        return None

    # Determine if the response is a directory or a value
    if response.text.endswith('/'):
        # It's a directory; recursively fetch nested paths
        nested_paths = response.text.strip().split('\n')
        result = {}
        for nested_path in nested_paths:
            nested_full_path = f"{path}{nested_path}"
            result[nested_path.replace('/', '')] = fetch_metadata(url, token, nested_full_path)
        return result
    else:
        # It's a value
        return response.text

def main():
    token = get_token()
    if token:
        metadata = fetch_metadata(METADATA_URL, token)
        if metadata:
            # Store the metadata in a cached file
            with open('ec2_metadata_cache.json', 'w') as file:
                json.dump(metadata, file, indent=4)
            logging.info("Successfully retrieved and cached EC2 instance metadata.")
        else:
            logging.error("Failed to retrieve any metadata.")
    else:
        logging.error("Could not obtain IMDSv2 token.")

if __name__ == "__main__":
    main()
