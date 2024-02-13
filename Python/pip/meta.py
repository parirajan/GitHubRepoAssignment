import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class MetadataFetcher:
    def __init__(self):
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.token = self.fetch_token()

    def fetch_token(self):
        response = requests.put("http://169.254.169.254/latest/api/token", headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"})
        if response.status_code == 200:
            return response.text
        else:
            logging.error("Failed to obtain IMDSv2 token")
            return None

    def fetch_metadata(self, path=''):
        headers = {"X-aws-ec2-metadata-token": self.token}
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        if response.status_code == 200:
            if response.text.endswith('/'):
                items = response.text.strip().split('\n')
                directory_content = {}
                for item in items:
                    nested_content = self.fetch_metadata(f"{path}{item}")
                    directory_content[item.rstrip('/')] = nested_content
                return directory_content
            else:
                return response.text
        else:
            logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status: {response.status_code}")
            return None

def main():
    fetcher = MetadataFetcher()
    all_metadata = fetcher.fetch_metadata()
    logging.info(all_metadata)

if __name__ == "__main__":
    main()
