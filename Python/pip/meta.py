import requests
import logging
import json
import boto3
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
class EC2MetadataFetcher:
    def __init__(self):
        self.token_url = "http://169.254.169.254/latest/"
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.token = self.fetch_token()
        self.instance_id = self.fetch_metadata("instance-id")
        self.region = self.fetch_metadata("placement/region")
        self.ec2_client = boto3.client('ec2', region_name=self.region)
    def fetch_token(self):
        """Fetches a token for IMDSv2 requests."""
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        response = requests.put(f"{self.base_url}api/token", headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logging.error(f"Failed to obtain IMDSv2 token, status code: {response.status_code}")
            raise Exception("Failed to obtain IMDSv2 token")
    def fetch_metadata(self, path=''):
        """Fetches metadata for a given path using the IMDSv2 token."""
        headers = {"X-aws-ec2-metadata-token": self.token}
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) == 1 and not lines[0].endswith('/'):
                # Single line, not a directory, return as final value
                return response.text.strip()
            elif all(not line.endswith('/') for line in lines):
                # Treat each line as an attribute and fetch its value
                attribute_values = {}
                for line in lines:
                    if line:  # Non-empty line
                        value = self.fetch_metadata(f"{path}{line}")
                        attribute_values[line] = value
                return attribute_values
            else:
                # Directory-like or mixed content, recurse
                content = {}
                for line in lines:
                    if line:  # Non-empty line
                        nested_content = self.fetch_metadata(f"{path}{line}")
                        content[line.rstrip('/')] = nested_content
                return content
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
