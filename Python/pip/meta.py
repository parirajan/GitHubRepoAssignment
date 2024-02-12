from ec2_metadata import ec2_metadata
import logging
import json

# Set up logging
logging.basicConfig(filename='metadata_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def is_fetchable_attribute(attribute_name):
    """
    Determine if the attribute is a fetchable metadata attribute.
    This filters out methods and special properties of the ec2_metadata object.
    """
    # Exclude special attributes and methods
    if attribute_name.startswith('__') or callable(getattr(ec2_metadata, attribute_name)):
        return False
    return True

def fetch_metadata():
    metadata_dict = {}
    attributes = dir(ec2_metadata)
    fetchable_attributes = [attr for attr in attributes if is_fetchable_attribute(attr)]

    for attr in fetchable_attributes:
        try:
            # Dynamically get attribute value
            value = getattr(ec2_metadata, attr, None)
            if value:
                metadata_dict[attr] = value
        except Exception as e:
            logging.error(f"Error retrieving metadata for {attr}: {str(e)}")

    # Store the metadata in a cached file
    with open('ec2_metadata_cache.json', 'w') as file:
        json.dump(metadata_dict, file, indent=4)

    logging.info("Successfully retrieved and cached EC2 instance metadata.")

def main():
    fetch_metadata()

if __name__ == "__main__":
    main()
