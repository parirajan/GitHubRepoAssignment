import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class EC2MetadataFetcher:
    TOKEN_URL = "http://169.254.169.254/latest/api/token"
    METADATA_URL = "http://169.254.169.254/latest/meta-data/"

    def __init__(self):
        self.token = self._fetch_imdsv2_token()

    def _fetch_imdsv2_token(self):
        """
        Fetches a token for IMDSv2 requests.
        """
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        response = requests.put(self.TOKEN_URL, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logging.error("Failed to fetch IMDSv2 token")
            return None

    def fetch_metadata(self, path=''):
        """
        Recursively fetch metadata, handling directory-like structures and parsing JSON where appropriate.
        """
        headers = {"X-aws-ec2-metadata-token": self.token}
        url = f"{self.METADATA_URL}{path}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if content_type == 'application/json':
                # If the content is JSON, parse it
                return response.json()
            elif response.text.endswith('/'):
                # It's a directory; list contents and recurse
                items = response.text.strip().split('\n')
                directory_content = {}
                for item in items:
                    if item:  # Skip empty items
                        directory_content[item] = self.fetch_metadata(f"{path}{item}")
                return directory_content
            else:
                # It's a final value
                return response.text
        else:
            logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status: {response.status_code}")
            return None

def main():
    metadata_fetcher = EC2MetadataFetcher()
    metadata = metadata_fetcher.fetch_metadata()
    logging.info("Fetched EC2 instance metadata:")
    logging.info(metadata)

if __name__ == "__main__":
    main()
