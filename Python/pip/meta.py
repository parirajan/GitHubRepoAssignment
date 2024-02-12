import json
import logging
from botocore.utils import IMDSFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class RecursiveIMDSFetcher:
    def __init__(self):
        self.fetcher = IMDSFetcher()
        self.token = self.fetcher._fetch_metadata_token()

    def fetch_metadata(self, path=''):
        """
        Recursively fetch metadata from a given path.
        """
        metadata = {}
        data = self.fetcher.retrieve_metadata(path, self.token)
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) or isinstance(value, list):
                    # Recursive case: the item is a directory-like structure
                    metadata[key] = self.fetch_metadata(f"{path}{key}/")
                else:
                    # Base case: the item is a final value
                    metadata[key] = value
        elif isinstance(data, list) and path:
            # Special handling for lists, typically at the end of a path
            return data
        elif data and path:
            # Base case for direct value retrieval
            return data
        return metadata

    def fetch_all_metadata(self):
        """
        Fetch all available metadata starting from the root.
        """
        return self.fetch_metadata()

def main():
    fetcher = RecursiveIMDSFetcher()
    metadata = fetcher.fetch_all_metadata()
    
    # Store the fetched metadata in a JSON file
    with open('ec2_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    
    logging.info("Successfully fetched and stored EC2 instance metadata.")

if __name__ == "__main__":
    main()
