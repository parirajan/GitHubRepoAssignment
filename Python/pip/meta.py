import json
import logging
from ec2_metadata import ec2_metadata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the cache file path
CACHE_FILE = 'ec2_metadata_cache.json'

def cache_metadata(metadata, file_path):
    """
    Cache metadata to a JSON file.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(metadata, file)
        logging.info("Metadata cached successfully.")
    except Exception as e:
        logging.error(f"Failed to cache metadata: {e}")

def fetch_all_metadata():
    """
    Fetch all available EC2 instance metadata and cache it in a JSON file.
    """
    try:
        # Using the ec2_metadata library to fetch all available metadata
        metadata = {
            'ami_id': ec2_metadata.ami_id,
            'ami_launch_index': ec2_metadata.ami_launch_index,
            'ami_manifest_path': ec2_metadata.ami_manifest_path,
            'block_device_mapping': ec2_metadata.block_device_mapping,
            'hostname': ec2_metadata.hostname,
            'instance_action': ec2_metadata.instance_action,
            'instance_id': ec2_metadata.instance_id,
            'instance_life_cycle': ec2_metadata.instance_life_cycle,
            'instance_type': ec2_metadata.instance_type,
            'local_hostname': ec2_metadata.local_hostname,
            'local_ipv4': ec2_metadata.local_ipv4,
            'mac': ec2_metadata.mac,
            'metrics': ec2_metadata.metrics,
            'network': ec2_metadata.network,
            'placement': ec2_metadata.placement,
            'profile': ec2_metadata.profile,
            'public_hostname': ec2_metadata.public_hostname,
            'public_ipv4': ec2_metadata.public_ipv4,
            'public_keys': ec2_metadata.public_keys,
            'reservation_id': ec2_metadata.reservation_id,
            'security_groups': ec2_metadata.security_groups,
            # ... include other metadata properties as needed
        }
        logging.info("Successfully fetched all instance metadata.")
        cache_metadata(metadata, CACHE_FILE)
    except Exception as e:
        logging.error(f"An error occurred while fetching metadata: {e}")

# Example usage
fetch_all_metadata()
