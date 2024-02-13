import unittest
from moto import mock_ec2
import boto3
from ec2_metadata_fetcher import EC2MetadataFetcher  # Adjusted import

class TestEC2MetadataFetcher(unittest.TestCase):
    @mock_ec2
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

