import unittest
from unittest.mock import patch
import json
import os
from moto import mock_ec2
import boto3
from your_script_name import EC2MetadataFetcher  # Adjust the import path as necessary

class TestEC2MetadataFetcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for class"""
        cls.cache_file = 'ec2_metadata_and_tags_cache.json'

    def setUp(self):
        """Ensure the cache file does not exist before each test"""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def tearDown(self):
        """Clean up by removing the cache file after each test"""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    @patch('requests.put')
    @patch('requests.get')
    def test_fetch_metadata_success(self, mock_get, mock_put):
        """Test fetching metadata successfully"""
        mock_put.return_value.text = 'test-token'
        mock_put.return_value.status_code = 200
        mock_get.return_value.text = 'test-instance-id'
        mock_get.return_value.status_code = 200

        fetcher = EC2MetadataFetcher()
        instance_id = fetcher.fetch_metadata("instance-id")
        self.assertEqual(instance_id, 'test-instance-id')

    @patch('requests.put')
    @patch('requests.get')
    def test_fetch_metadata_failure(self, mock_get, mock_put):
        """Test fetching metadata with failure"""
        mock_put.return_value.text = 'test-token'
        mock_put.return_value.status_code = 200
        mock_get.return_value.status_code = 404

        fetcher = EC2MetadataFetcher()
        instance_id = fetcher.fetch_metadata("instance-id")
        self.assertIsNone(instance_id)

    @mock_ec2
    def test_fetch_instance_tags_success(self):
        """Test fetching instance tags successfully"""
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        instance = ec2.create_instances(ImageId='ami-12345678', MinCount=1, MaxCount=1)[0]
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': 'TestInstance'}])

        with patch('your_script_name.EC2MetadataFetcher.fetch_metadata') as mock_fetch_metadata:
            mock_fetch_metadata.side_effect = ['i-1234567890abcdef0', 'us-east-1']
            fetcher = EC2MetadataFetcher()
            tags = fetcher.fetch_instance_tags()
            self.assertEqual(tags, {'Name': 'TestInstance'})

    @mock_ec2
    def test_fetch_instance_tags_failure(self):
        """Test fetching instance tags with failure"""
        with patch('boto3.client') as mock_client:
            mock_client.return_value.describe_tags.side_effect = Exception("AWS Error")
            with patch('your_script_name.EC2MetadataFetcher.fetch_metadata') as mock_fetch_metadata:
                mock_fetch_metadata.side_effect = ['i-1234567890abcdef0', 'us-east-1']
                fetcher = EC2MetadataFetcher()
                tags = fetcher.fetch_instance_tags()
                self.assertEqual(tags, {})

    def test_cache_file_creation_and_content(self):
        """Test cache file creation and JSON content"""
        # Assuming a method in EC2MetadataFetcher to write the cache file
        fetcher = EC2MetadataFetcher()
        fetcher.main()  # Adjust this to call the actual method that writes the cache file
        
        self.assertTrue(os.path.exists(self.cache_file), "Cache file was not created.")
        
        with open(self.cache_file, 'r') as file:
            data = json.load(file)
            self.assertIsInstance(data, dict)

if __name__ == '__main__':
    unittest.main()
