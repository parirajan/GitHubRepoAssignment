import requests
import logging
import json
import boto3
from unittest.mock import patch, MagicMock
import unittest
from moto import mock_ec2

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

class EC2MetadataFetcher:
    def __init__(self):
        self.token_url = "http://169.254.169.254/latest/api/token"
        self.base_url = "http://169.254.169.254/latest/meta-data/"
        self.token = self.fetch_token()
        self.instance_id = self.fetch_metadata("instance-id")
        self.region = self.fetch_metadata("placement/region")
        self.ec2_client = boto3.client('ec2', region_name=self.region)

    def fetch_token(self):
        """Fetches a token for IMDSv2 requests."""
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        response = requests.put(self.token_url, headers=headers)
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
                Filters=[{'Name': 'resource-id', 'Values': [self.instance_id]}]
            )
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
        except Exception as e:
            logging.error(f"Failed to fetch instance tags: {e}")
            return {}

def main():
    fetcher = EC2MetadataFetcher()
    metadata = fetcher.fetch_metadata()
    tags = fetcher.fetch_instance_tags()
    logging.info("Fetched EC2 instance metadata and tags successfully.")
    full_metadata = {'metadata': metadata, 'tags': tags}
    with open('ec2_metadata_and_tags_cache.json', 'w') as file:
        json.dump(full_metadata, file, indent=4)
    logging.info("Metadata and tags stored in ec2_metadata_and_tags_cache.json.")

class TestEC2MetadataFetcher(unittest.TestCase):
    cache_file = 'ec2_metadata_and_tags_cache.json'

    def setUp(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    @patch('requests.put')
    @patch('requests.get')
    def test_fetch_metadata_success(self, mock_get, mock_put):
        mock_put.return_value = MagicMock(status_code=200, text='test-token')
        mock_get.return_value = MagicMock(status_code=200, text='test-instance-id')
        fetcher = EC2MetadataFetcher()
        instance_id = fetcher.fetch_metadata("instance-id")
        self.assertEqual(instance_id, 'test-instance-id')

    @mock_ec2
    def test_fetch_instance_tags_success(self):
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        instance = ec2.create_instances(ImageId='ami-12345678', MinCount=1, MaxCount=1)[0]
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': 'TestInstance'}])
        with patch('requests.put'), patch('requests.get', return_value=MagicMock(text='us-east-1', status_code=200)):
            fetcher = EC2MetadataFetcher()
            tags = fetcher.fetch_instance_tags()
            self.assertEqual(tags, {'Name': 'TestInstance'})

if __name__ == '__main__':
    unittest.main()
