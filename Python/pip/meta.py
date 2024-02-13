import logging
import json
from botocore.utils import IMDSFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def fetch_metadata_token():
    """
    Use IMDSFetcher to fetch an EC2 metadata token.
    """
    fetcher = IMDSFetcher()
    token = fetcher._fetch_metadata_token()  # Note: Using a protected method
    return token

def list_metadata_attributes(token):
    """
    List attributes under /latest/meta-data/ and return them as a dictionary.
    """
    metadata_dict = {}
    fetcher = IMDSFetcher()
    example_paths = ['ami-id', 'instance-type', 'instance-id']

    for path in example_paths:
        try:
            response = fetcher._get_request(f"/latest/meta-data/{path}", None, token=token)
            if response.status_code == 200:
                # Assuming all responses are plain text for these paths
                metadata_dict[path] = response.text
            else:
                logging.error(f"Failed to fetch /latest/meta-data/{path}, HTTP status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Exception while fetching /latest/meta-data/{path}: {e}")

    return metadata_dict

def main():
    token = fetch_metadata_token()
    if token:
        logging.info("Successfully fetched EC2 metadata token.")
        metadata = list_metadata_attributes(token)
        # Cache the metadata as JSON in a file
        with open('ec2_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=4)
        logging.info("Metadata cached as ec2_metadata.json.")
    else:
        logging.error("Failed to fetch EC2 metadata token.")

if __name__ == "__main__":
    main()
