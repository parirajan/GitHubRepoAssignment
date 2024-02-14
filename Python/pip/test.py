import unittest
from unittest.mock import patch, MagicMock
import os
from ec2_metadata_fetcher import EC2MetadataFetcher

class TestEC2MetadataFetcher(unittest.TestCase):
    cache_file = 'ec2_metadata_and_tags_cache.json'

    def setUp(self):
        # Ensure the cache file does not exist before each test
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def tearDown(self):
        # Clean up by removing the cache file after each test
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    @patch('requests.put')
    @patch('requests.get')
    def test_fetch_token_and_metadata(self, mock_get, mock_put):
        # Mock the response for obtaining IMDSv2 token
        mock_put.return_value = MagicMock(status_code=200, text='mock-token')
        # Mock the response for fetching metadata
        mock_get.side_effect = [
            MagicMock(status_code=200, text='i-1234567890abcdef0'),  # instance-id
            MagicMock(status_code=200, text='us-east-1'),  # region
            # Add more mocked responses for other metadata paths if needed
        ]

        fetcher = EC2MetadataFetcher()
        self.assertEqual(fetcher.instance_id, 'i-1234567890abcdef0')
        self.assertEqual(fetcher.region, 'us-east-1')

    @patch('boto3.client')
    def test_fetch_instance_tags(self, mock_client):
        # Mock the EC2 client's describe_tags method
        mock_client.return_value.describe_tags.return_value = {
            'Tags': [
                {'Key': 'Name', 'Value': 'TestInstance'},
                {'Key': 'Environment', 'Value': 'Development'}
            ]
        }

        fetcher = EC2MetadataFetcher()
        tags = fetcher.fetch_instance_tags()
        self.assertEqual(tags, {'Name': 'TestInstance', 'Environment': 'Development'})

    @patch('builtins.open')
    @patch('json.dump')
    def test_cache_file_creation_and_content(self, mock_dump, mock_open):
        # Mock open and json.dump to simulate file writing
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        fetcher = EC2MetadataFetcher()
        fetcher.fetch_instance_tags = MagicMock(return_value={'Name': 'TestInstance'})
        fetcher.fetch_metadata = MagicMock(return_value='mocked-metadata')
        main()

        # Verify that open was called to write the cache file
        mock_open.assert_called_once_with(self.cache_file, 'w')
        # Verify json.dump was called with the expected data structure
        expected_data = {
            'metadata': 'mocked-metadata',
            'tags': {'Name': 'TestInstance'}
        }
        mock_dump.assert_called_once_with(expected_data, mock_open.return_value.__enter__.return_value, indent=4)

if __name__ == '__main__':
    unittest.main()
