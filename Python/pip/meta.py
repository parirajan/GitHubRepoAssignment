import requests
import logging
import time
from botocore.utils import IMDSFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class RecursiveMetadataFetcher:
    def __init__(self, retry_limit=3):
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.fetcher = IMDSFetcher()
        self.token = None
        self.token_time = None
        self.retry_limit = retry_limit

    def fetch_metadata_token(self):
        """
        Fetch a new IMDSv2 token and update the token time.
        """
        self.token = self.fetcher._fetch_metadata_token()
        self.token_time = time.time()

    def is_token_valid(self):
        """
        Check if the existing token is still valid (less than 1 minute old).
        """
        if self.token and (time.time() - self.token_time) < 60:
            return True
        return False

    def fetch_path(self, path='', retries=0):
        """
        Fetch metadata for a given path, managing token validity and retry attempts.
        """
        if not self.is_token_valid() or not self.token:
            self.fetch_metadata_token()
        
        response = self.fetcher._get_request(f"{self.base_url}{path}", None, token=self.token)
        if response.status_code == 200:
            return response.text
        else:
            if retries < self.retry_limit:
                logging.info(f"Retrying path: {path}, attempt {retries + 1}")
                return self.fetch_path(path, retries + 1)
            else:
                logging.error(f"Exceeded retries for path: {path}, HTTP status: {response.status_code}")
                return None

    def list_and_fetch(self, current_path=''):
        """
        Recursively list all metadata paths and fetch their contents, respecting token lifespan and retry limits.
        """
        metadata_contents = self.fetch_path(current_path)
        if metadata_contents:
            if metadata_contents.endswith('/'):
                items = metadata_contents.strip().split('\n')
                result = {}
                for item in items:
                    if item:  # Prevent fetching empty paths
                        nested_result = self.list_and_fetch(f"{current_path}{item}")
                        result[item] = nested_result
                return result
            else:
                return metadata_contents
        return None

def main():
    metadata_fetcher = RecursiveMetadataFetcher(retry_limit=3)
    metadata = metadata_fetcher.list_and_fetch()
    logging.info(f"Metadata: {metadata}")

if __name__ == "__main__":
    main()
