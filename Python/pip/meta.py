from ec2_metadata import ec2_metadata
import logging
import json

# Set up logging
logging.basicConfig(filename='metadata_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def is_fetchable_attribute(attribute_name):
    """
    Determine if the attribute is a fetchable metadata attribute.
    This filters out methods, special properties of the ec2_metadata object, and
    excludes IAM security credentials and instance profile ARN.
    """
    # Exclude special attributes and methods, IAM security credentials, and instance profile ARN
    excluded_attributes = ['__', 'callable', 'iam_security_credentials', 'iam_info']
    if any(excl in attribute_name for excl in excluded_attributes):
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
                # Exclude IAM security credentials and instance profile ARN explicitly
                if attr not in ['iam_security_credentials', 'iam_info']:
                    metadata_dict[attr] = value
        except Exception as e:
            logging.error(f"Error retrieving metadata for {attr}: {str(e)}")

    # Store the metadata in a cached file
    with open('ec2_metadata_cache.json', 'w') as file:
        json.dump(metadata_dict, file, indent=4)

    logging.info("Successfully retrieved and cached EC2 instance metadata, excluding IAM security credentials and instance profile ARN.")

def main():
    fetch_metadata()

if __name__ == "__main__":
    main()
