import requests
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class MetadataFetcher:
    def __init__(self):
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.token = self.fetch_token()

    def fetch_token(self):
        """
        Fetches a token for IMDSv2 requests.
        """
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        response = requests.put("http://169.254.169.254/latest/api/token", headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logging.error("Failed to obtain IMDSv2 token")
            raise Exception("Failed to obtain IMDSv2 token")

    def fetch_metadata(self, path=''):
        """Improved fetch_metadata with error handling for retry logic."""
        headers = {"X-aws-ec2-metadata-token": self.token}
        try:
            response = requests.get(f"{self.base_url}{path}", headers=headers, timeout=5)  # Added timeout for safety
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if any(line.endswith('/') for line in lines):
                    directory_content = {item.rstrip('/'): self.fetch_metadata(f"{path}{item}") for item in lines if item}
                    return directory_content
                else:
                    return response.text.strip()
            else:
                logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for path: '{path}', Error: {e}")
        return None

def main():
    fetcher = MetadataFetcher()
    all_metadata = fetcher.fetch_metadata()
    logging.info("Fetched EC2 instance metadata successfully.")

    # Store the fetched metadata in a JSON cache file
    with open('ec2_metadata_cache.json', 'w') as cache_file:
        json.dump(all_metadata, cache_file, indent=4)
    logging.info("Metadata stored in ec2_metadata_cache.json.")

if __name__ == "__main__":
    main()
