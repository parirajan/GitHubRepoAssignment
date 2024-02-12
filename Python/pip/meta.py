import requests
import logging
from botocore.utils import IMDSFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class RecursiveMetadataFetcher:
    def __init__(self):
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.fetcher = IMDSFetcher()
        self.token = self.fetcher._fetch_metadata_token()
    
    def fetch_path(self, path=''):
        """
        Fetch metadata for a given path using IMDSFetcher._get_request.
        """
        full_path = f"{self.base_url}{path}"
        response = self.fetcher._get_request(full_path, None, token=self.token)
        if response.status_code == 200:
            return response.text
        else:
            logging.error(f"Error fetching path: {path}, HTTP status: {response.status_code}")
            return None

    def list_and_fetch(self, current_path=''):
        """
        Recursively list all metadata paths and fetch their contents.
        """
        metadata_contents = self.fetch_path(current_path)
        if metadata_contents:
            # Check if the response contains a list of items (indicative of a directory)
            if metadata_contents.endswith('/'):
                items = metadata_contents.strip().split('\n')
                result = {}
                for item in items:
                    if item:  # Ensure it's not an empty string
                        nested_result = self.list_and_fetch(f"{current_path}{item}")
                        result[item] = nested_result
                return result
            else:
                return metadata_contents
        return None

def main():
    metadata_fetcher = RecursiveMetadataFetcher()
    metadata = metadata_fetcher.list_and_fetch()
    logging.info(f"Metadata: {metadata}")

    # Optionally, save the metadata to a JSON file
    # This part is left as an exercise

if __name__ == "__main__":
    main()
