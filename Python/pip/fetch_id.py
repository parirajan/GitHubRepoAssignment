import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def get_ami_id_from_cache(cache_file_path='ec2_metadata_cache.json'):
    """
    Reads the cached EC2 metadata from a JSON file and returns the AMI ID.
    
    :param cache_file_path: Path to the JSON cache file containing EC2 metadata.
    :return: The AMI ID if found, otherwise None.
    """
    try:
        with open(cache_file_path, 'r') as cache_file:
            metadata = json.load(cache_file)
            # Assuming 'ami-id' is at the top-level in the cached metadata
            ami_id = metadata.get('ami-id', None)
            return ami_id
    except FileNotFoundError:
        logging.error(f"Cache file not found: {cache_file_path}")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the cache file: {cache_file_path}")
    except Exception as e:
        logging.error(f"Unexpected error reading cache file: {e}")
    return None

def main():
    ami_id = get_ami_id_from_cache()
    if ami_id:
        logging.info(f"AMI ID from cache: {ami_id}")
    else:
        logging.error("Failed to retrieve AMI ID from cache.")

if __name__ == "__main__":
    main()
