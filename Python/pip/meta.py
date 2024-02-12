import json
import logging
from botocore.utils import IMDSFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class CustomIMDSFetcher:
    def __init__(self):
        self.fetcher = IMDSFetcher()
        self.token = self.fetcher._fetch_metadata_token()

    def _recursive_fetch(self, path):
        """
        Recursively fetch metadata using _get_request and construct a nested dictionary.
        """
        full_path = f"/latest/meta-data/{path}"
        response = self.fetcher._get_request(full_path, None, token=self.token)
        if response.status_code == 200:
            text = response.text
            # Check if the response is directory-like or a final value
            if text.endswith('/'):
                # Directory-like response, split and recurse
                items = text.strip().split('\n')
                result = {}
                for item in items:
                    if item:  # Ensure non-empty
                        nested_path = f"{path}{item}/" if path else f"{item}/"
                        result[item] = self._recursive_fetch(nested_path)
                return result
            else:
                # Final value, return directly
                return text
        else:
            logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status code: {response.status_code}")
            return None

    def fetch_all_metadata(self):
        """
        Fetch all available metadata starting from the root.
        """
        return self._recursive_fetch('')

def main():
    custom_fetcher = CustomIMDSFetcher()
    metadata = custom_fetcher.fetch_all_metadata()
    
    # Store the fetched metadata in a JSON file
    with open('ec2_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    
    logging.info("Successfully fetched and stored EC2 instance metadata.")

if __name__ == "__main__":
    main()
