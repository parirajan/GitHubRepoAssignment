from ec2_metadata import ec2_metadata
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def fetch_metadata():
    metadata_dict = {}
    # List all attributes of the ec2_metadata object
    attributes = dir(ec2_metadata)

    for attr in attributes:
        if not attr.startswith('_') and not callable(getattr(ec2_metadata, attr)):
            try:
                # Dynamically access the attribute
                value = getattr(ec2_metadata, attr, 'Attribute not found')
                # Some attributes might be callable methods that provide metadata, handle those separately if needed
                if value != 'Attribute not found':
                    metadata_dict[attr] = value
            except Exception as e:
                logging.error(f"Error accessing metadata for attribute '{attr}': {e}")

    # Store the successfully retrieved metadata in a cached file
    with open('ec2_metadata_cache.json', 'w') as file:
        json.dump(metadata_dict, file, indent=4)

    logging.info("Successfully retrieved and cached EC2 instance metadata.")

def main():
    fetch_metadata()

if __name__ == "__main__":
    main()
