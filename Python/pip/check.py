from ec2_metadata import ec2_metadata
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def fetch_iam_security_credentials():
    try:
        # Attempt to access IAM security credentials
        iam_info = ec2_metadata.iam_info
        logging.info("IAM Info: %s", iam_info)

        # IAM security credentials are under a role name, which we need to extract first
        role_name = list(ec2_metadata.iam_security_credentials.keys())[0]
        credentials = ec2_metadata.iam_security_credentials[role_name]
        logging.info("IAM Credentials: %s", credentials)
    except AttributeError:
        logging.error("IAM security credentials not found. This instance may not have an IAM role assigned.")
    except Exception as e:
        logging.error(f"Error fetching IAM security credentials: {e}")

def main():
    fetch_iam_security_credentials()

if __name__ == "__main__":
    main()
