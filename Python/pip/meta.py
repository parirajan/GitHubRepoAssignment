import requests
import json
import logging

# Set up logging
logging.basicConfig(filename='metadata_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

METADATA_URL = "http://169.254.169.254/latest/meta-data/"
TOKEN_URL = "http://169.254.169.254/latest/api/token"

def get_token():
    headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    response = requests.put(TOKEN_URL, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logging.error("Failed to retrieve IMDSv2 token")
        return None

def fetch_metadata(url, token, current_path=''):
    headers = {"X-aws-ec2-metadata-token": token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to fetch metadata for path: {current_path}")
        return None

    # Check if the response is text or a directory listing
    text = response.text
    if text.endswith('/'):
        # Directory listing, we need to recursively fetch each path
        items = text.split('\n')
        result = {}
        for item in items:
            if item:  # Avoid empty strings
                new_path = f"{current_path}{item}"
                result[item] = fetch_metadata(f"{url}{item}", token, new_path)
        return result
    else:
        return text

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
