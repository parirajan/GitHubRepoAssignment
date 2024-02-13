import requests
import logging

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
        """
        Recursively fetch metadata, correctly handling both directory-like structures and final values.
        """
        headers = {"X-aws-ec2-metadata-token": self.token}
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Check if the response is a directory (ends with '/')
            if any(line.endswith('/') for line in response.text.strip().split('\n')):
                # Directory-like response: Recurse into each item
                items = response.text.strip().split('\n')
                directory_content = {}
                for item in items:
                    if item:  # Non-empty
                        # Recursively fetch nested metadata
                        nested_path = f"{path}{item}"
                        nested_content = self.fetch_metadata(nested_path)
                        # Remove trailing slash for directory names
                        directory_content[item.rstrip('/')] = nested_content
                return directory_content
            else:
                # Final value: Return as is
                return response.text.strip()
        else:
            logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status: {response.status_code}")
            return None

def main():
    fetcher = MetadataFetcher()
    all_metadata = fetcher.fetch_metadata()
    logging.info("Fetched EC2 instance metadata successfully.")
    for key, value in all_metadata.items():
        logging.info(f"{key}: {value}")

if __name__ == "__main__":
    main()
