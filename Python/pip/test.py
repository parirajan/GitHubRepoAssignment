import requests
import logging
import json
import boto3
import unittest
from moto import mock_ec2
from unittest.mock import patch

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
        response = requests.put(f"{self.token_url}api/token", headers=headers)
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

# Assuming the main functionality and caching logic are encapsulated in this function
def main():
    fetcher = EC2MetadataFetcher()
    # Additional functionality to fetch metadata and tags, then cache them
    # Similar to the provided script

class TestEC2MetadataFetcher(unittest.TestCase):
    # The provided test class implementation goes here

if __name__ == '__main__':
    # Conditionally run tests or main functionality based on the execution context
    # For example, you might check for a command-line argument to decide whether to run tests
    unittest.main()
