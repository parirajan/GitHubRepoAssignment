from ec2_metadata import ec2_metadata
import logging
import json

# Set up logging
logging.basicConfig(filename='metadata_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def is_fetchable_attribute(attribute_name):
    """
    Determine if the attribute is a fetchable metadata attribute.
    This filters out methods and special properties of the ec2_metadata object.
    Additionally, ensure that the attribute is not a method and is serializable.
    """
    # Exclude methods and non-serializable properties
    if attribute_name.startswith('__'):
        return False
    attr = getattr(ec2_metadata, attribute_name, None)
    if callable(attr) or attribute_name in ['iam_security_credentials', 'iam_info']:
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
            # Convert the value to a JSON-serializable format if necessary
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                metadata_dict[attr] = value
            else:
                # Attempt to convert custom objects to string or a serializable dict
                metadata_dict[attr] = str(value)
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
