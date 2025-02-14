import os
import json
import subprocess
import base64
import requests
from datetime import datetime, timedelta
import boto3
import re
import botocore.exceptions

# AWS S3 Configuration
S3_BUCKET = "s3buckettest"
TRACKER_FOLDER = "sp/206/tracker/"
VERSION_FOLDER = "sp/106/version/"
JOURNAL_S3_PREFIX = "sp/206/journals/"
LOCAL_STORAGE = "/persistent/data/journal/import/"
IMPORT_SCRIPT = "/opt/ibm/safer_payments/ccm/run.pyc"
LOCAL_FOLDER = "/opt/ibm/safer_payments/ccm/"

# Consul Configuration
CONSUL_ENDPOINT = "https://localhost:8501/v1/kv/config/infra-fraud-sp,aws/exec.version"
CONSUL_ACL_FILE = "/etc/consul.d/acl.hcl"

# Set the latest version file dynamically
source_cluster_id = 206
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
LOCAL_VERSION_FILE = f"{LOCAL_FOLDER}version-{CURRENT_DATE}.json"

s3_client = boto3.client("s3")

def get_consul_acl_token():
    """Retrieve the Consul ACL token from the ACL configuration file."""
    acl_file = CONSUL_ACL_FILE

    try:
        with open(acl_file, "r") as f:
            for line in f:
                line = line.strip()
                match = re.search(r'agent\s*=\s*"([^"]+)"', line)
                if match:
                    return match.group(1)  # Extract and return the token
    except FileNotFoundError:
        print(f"ACL file not found at {acl_file}.")
    
    print("Error: Could not find ACL token in the file.")
    return None  # Return None if token is missing


def get_consul_target():
    """Fetch and decode the target version from Consul KV."""
    acl_token = get_consul_acl_token()
    if not acl_token:
        print("Error: No ACL token found.")
        return None

    headers = {"X-Consul-Token": acl_token}
    try:
        response = requests.get(CONSUL_ENDPOINT, headers=headers, verify=False)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0 and "Value" in data[0]:
                decoded_value = base64.b64decode(data[0]["Value"]).decode("utf-8")
                return json.loads(decoded_value)

            print("Error: Consul KV response does not contain a valid JSON value.")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Consul: {e}")

    return None

# Fetch a JSON file from S3
def fetch_s3_json(s3_bucket, s3_key):
    try:
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"File {s3_key} not found in S3.")
        return None


def get_s3_version_file():
    return fetch_s3_json(S3_BUCKET, f"{VERSION_FOLDER}version-{CURRENT_DATE}.json")


def get_s3_tracker(tracker_filename):
    return fetch_s3_json(S3_BUCKET, f"{TRACKER_FOLDER}{tracker_filename}")


# Fetch the earliest or latest journal file from S3
def fetch_s3_journal(date=None, earliest=False):
    prefix = f"{JOURNAL_S3_PREFIX}{date}/" if date else JOURNAL_S3_PREFIX
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

    if "Contents" in response:
        sorted_journals = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=not earliest)
        journal = sorted_journals[0]
        print(f"Found journal: {journal['Key']}")
        return journal["Key"]

    print(f"No journal files found for {date if date else 'all time'} in S3.")
    return None


def get_earliest_s3_journal():
    return fetch_s3_journal(earliest=True)


def get_latest_s3_journal(date):
    return fetch_s3_journal(date=date, earliest=False)


def find_closest_version(tracker_data, target_time):
    target_dt = datetime.strptime(target_time, "%H:%M")

    valid_versions = [
        (datetime.strptime(entry["timestamp"].split()[-1], "%H:%M:%S"), entry)
        for entry in tracker_data if datetime.strptime(entry["timestamp"].split()[-1], "%H:%M:%S") < target_dt
    ]

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    return max(valid_versions, key=lambda x: x[0])[1]  # Return latest before target_time


def download_journal(s3_path, version_id):
    if not s3_path:
        print("Error: S3 path is None, skipping download.")
        return None

    file_name = os.path.basename(s3_path)
    local_path = os.path.join(LOCAL_STORAGE, file_name)

    print(f"Downloading {file_name} from S3 path: {s3_path} (Version: {version_id})...")

    try:
        extra_args = {"VersionId": version_id} if version_id else {}
        s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path, ExtraArgs=extra_args)

        print(f"Downloaded {file_name} to {local_path}")
        return local_path
    except botocore.exceptions.ClientError as e:
        print(f"AWS ClientError: {e}")
    except botocore.exceptions.EndpointConnectionError:
        print(f"Network Error: Failed to connect to AWS S3 endpoint.")
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")

    return None


def run_import_script(file_paths):
    if not file_paths:
        print("No files to import. Skipping import script.")
        return False

    if isinstance(file_paths, str):
        file_paths = [file_paths]

    script_dir = os.path.dirname(IMPORT_SCRIPT)
    command = ["python", IMPORT_SCRIPT] + file_paths

    try:
        print(f"Running import script for {len(file_paths)} files...")
        result = subprocess.run(command, cwd=script_dir, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Import script ran successfully for batch of {len(file_paths)} files.")
            return True
        else:
            print(f"ERROR: Import script failed.\n{result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to execute import script: {e}")
        return False


# Process Journal Sync
def process_journal_sync():
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")

    if not get_s3_version_file():
        print("ERROR: status.json is missing or corrupted. Aborting import.")
        return

    current_version = get_s3_version_file()
    if current_version and current_version.get("file"):
        current_version_date = current_version["file"].split("_")[-1].split(".")[0]
    else:
        current_version_date = None

    missing_journals = []

    if not current_version_date:
        print("No previous version found. Fetching latest available journal.")
        earliest_s3_path = get_earliest_s3_journal()

        if earliest_s3_path:
            current_version_date = earliest_s3_path.split("_")[-1].split(".")[0]
            missing_journals.append((earliest_s3_path, None))
        else:
            print("No journals found in S3, cannot proceed.")
            return

    current_date = datetime.strptime(current_version_date, "%Y-%m-%d")
    target_date = datetime.strptime(target_version_date, "%Y-%m-%d")

    while current_date < target_date:
        s3_path = get_latest_s3_journal(current_date.strftime("%Y-%m-%d"))
        if s3_path:
            missing_journals.append((s3_path, None))
        current_date += timedelta(days=1)

    tracker_filename = f"tracker_{target_version_date}_{source_cluster_id}.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if s3_tracker:
        closest_entry = find_closest_version(s3_tracker, target_version_time)
        if closest_entry:
            missing_journals.append((closest_entry["s3_path"], closest_entry["version_id"]))

    downloaded_files = [download_journal(s3_path, version_id) for s3_path, version_id in missing_journals if s3_path]

    if downloaded_files:
        print(f"Importing batch of {len(downloaded_files)} files...")

        if run_import_script(downloaded_files):
            for downloaded_file in downloaded_files:
                update_local_version(downloaded_file)

    print("Journal sync and import process completed successfully.")
