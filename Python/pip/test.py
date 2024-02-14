import unittest
from moto import mock_ec2
import boto3
from ec2_metadata_fetcher import EC2MetadataFetcher  # Adjusted import

class TestEC2MetadataFetcher(unittest.TestCase):
    def setUp(self):
        # Mock IMDS responses
        self.mock_imds_responses = {
            'http://169.254.169.254/latest/api/token': 'test-token',
            'http://169.254.169.254/latest/meta-data/instance-id': 'i-1234567890abcdef0',
            'http://169.254.169.254/latest/meta-data/placement/region': 'us-east-1',
        }

    def mock_requests_put(self, url, *args, **kwargs):
        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code
        if url == 'http://169.254.169.254/latest/api/token':
            return MockResponse('test-token', 200)
        return MockResponse(None, 404)

    def mock_requests_get(self, url, headers, *args, **kwargs):
        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code
        if url in self.mock_imds_responses:
            return MockResponse(self.mock_imds_responses[url], 200)
        return MockResponse(None, 404)    
    @mock_ec2

    # Execute: Run your function to fetch and cache the metadata
    fetch_and_cache_ec2_metadata()

    # Verify: Check the cache file exists
    cache_file_path = 'ec2_instances_cache.json'
    assert os.path.exists(cache_file_path), "Cache file was not created"

    # Verify: Check the content of the cache file
    with open(cache_file_path, 'r') as f:
        data = json.load(f)
        # For simplicity, just checking if 'Reservations' key exists
        assert 'Reservations' in data, "Cache file does not contain expected data"

    # Cleanup: Remove the cache file after test
    os.remove(cache_file_path)
    
    def test_fetch_instance_tags(self):
        # Setup mock EC2 environment
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        instance = ec2.create_instances(ImageId='ami-12345678', MinCount=1, MaxCount=1)[0]
        
        # Add a tag to the instance
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': 'TestInstance'}])
        
        # Example of testing directly with boto3, you would replace this with your actual test
        # that instantiates EC2MetadataFetcher and calls fetch_instance_tags or similar method.
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        response = ec2_client.describe_tags(
            Filters=[
                {'Name': 'resource-id', 'Values': [instance.id]}
            ]
        )
        tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
        
        # Assert the tag is as expected
        self.assertEqual(tags.get('Name'), 'TestInstance')

if __name__ == '__main__':
    unittest.main()

