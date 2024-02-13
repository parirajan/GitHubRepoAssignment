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
    List attributes under /latest/meta-data/ and attempt to parse JSON content.
    """
    fetcher = IMDSFetcher()

    # Example metadata paths; these are typically plain text but demonstrate the concept
    example_paths = ['ami-id', 'instance-type', 'instance-id']

    for path in example_paths:
        try:
            response = fetcher._get_request(f"/latest/meta-data/{path}", None, token=token)
            if response.status_code == 200:
                try:
                    # Attempt to parse the response as JSON
                    data = json.loads(response.text)
                    logging.info(f"Content of /latest/meta-data/{path} (parsed as JSON): {data}")
                except json.JSONDecodeError:
                    # If response is not JSON, log as plain text
                    logging.info(f"Content of /latest/meta-data/{path}: {response.text}")
            else:
                logging.error(f"Failed to fetch /latest/meta-data/{path}, HTTP status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Exception while fetching /latest/meta-data/{path}: {e}")

def main():
    token = fetch_metadata_token()
    if token:
        logging.info("Successfully fetched EC2 metadata token.")
        list_metadata_attributes(token)
    else:
        logging.error("Failed to fetch EC2 metadata token.")

if __name__ == "__main__":
    main()
