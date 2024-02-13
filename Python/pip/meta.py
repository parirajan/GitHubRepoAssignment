import requests
import logging
import json
import boto3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class EC2MetadataFetcher:
    def __init__(self):
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.token = self.fetch_token()
        self.instance_id = self.fetch_metadata("instance-id")
        self.ec2_client = boto3.client('ec2')

    def fetch_token(self):
        """Fetches a token for IMDSv2 requests."""
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        response = requests.put(f"{self.base_url}api/token", headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logging.error("Failed to obtain IMDSv2 token")
            raise Exception("Failed to obtain IMDSv2 token")

    def fetch_metadata(self, path=''):
        """Fetches metadata for a given path using the IMDSv2 token."""
        headers = {"X-aws-ec2-metadata-token": self.token}
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        if response.status_code == 200:
            return response.text.strip()
        else:
            logging.error(f"Failed to fetch metadata for path: '{path}', HTTP status: {response.status_code}")
            return None

    def fetch_instance_tags(self):
        """Fetches EC2 instance tags using the EC2 DescribeTags API."""
        try:
            response = self.ec2_client.describe_tags(
                Filters=[
                    {'Name': 'resource-id', 'Values': [self.instance_id]}
                ]
            )
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
        except Exception as e:
            logging.error(f"Failed to fetch instance tags: {e}")
            return {}

def main():
    fetcher = EC2MetadataFetcher()
    all_metadata = fetcher.fetch_metadata()
    instance_tags = fetcher.fetch_instance_tags()
    logging.info("Fetched EC2 instance metadata and tags successfully.")

    # Combine metadata and tags into one dictionary
    full_metadata = {
        'metadata': all_metadata,
        'tags': instance_tags
    }

    # Store the combined metadata and tags in a JSON cache file
    with open('ec2_metadata_and_tags_cache.json', 'w') as cache_file:
        json.dump(full_metadata, cache_file, indent=4)
    logging.info("Metadata and tags stored in ec2_metadata_and_tags_cache.json.")

if __name__ == "__main__":
    main()
