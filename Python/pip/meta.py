from ec2_metadata import ec2_metadata
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def is_public_attribute(attribute_name):
    """
    Determine if the attribute is public (fetchable) metadata attribute.
    This example simply filters out callable methods and magic methods, 
    assuming these are what's considered 'private' in this context.
    """
    attribute = getattr(ec2_metadata, attribute_name, None)
    if callable(attribute) or attribute_name.startswith('__'):
        return False
    return True

def fetch_metadata_attributes():
    """
    Fetch metadata attributes and store them in a dictionary.
    """
    metadata_dict = {}
    attributes = dir(ec2_metadata)
    public_attributes = [attr for attr in attributes if is_public_attribute(attr)]

    for attr in public_attributes:
        try:
            value = getattr(ec2_metadata, attr)
            metadata_dict[attr] = value
        except Exception as e:
            logging.error(f"Failed to retrieve metadata for {attr}: {e}")

    return metadata_dict

def main():
    metadata = fetch_metadata_attributes()
    # Optionally, print or log the metadata for verification
    for key, value in metadata.items():
        logging.info(f"{key}: {value}")

    # If you need to store the metadata in a structured format (e.g., JSON), consider serialization here

if __name__ == "__main__":
    main()
