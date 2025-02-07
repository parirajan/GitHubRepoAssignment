import os
import json
import boto3
import subprocess
import requests
import base64
import re
from datetime import datetime, timedelta

# AWS S3 Configuration
S3_BUCKET = "your-bucket-name"
TRACKER_FOLDER = "tracker/"  # S3 prefix for source trackers
VERSION_FOLDER = "version/"  # S3 prefix for target versions
JOURNAL_S3_PREFIX = "journals/"  # S3 prefix for journal files
LOCAL_STORAGE = "/path/to/journal_files"
IMPORT_SCRIPT = "/path/to/import_script.sh"

# Consul Configuration
CONSUL_ENDPOINT = "https://url:8501/v1/kv/version"
CONSUL_ACL_FILE = "/etc/consul.d/acl.hcl"

s3_client = boto3.client("s3")

# Generate current date dynamically for version tracking
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
LOCAL_VERSION_FILE = f"/path/to/version-{CURRENT_DATE}.json"

def get_consul_acl_token():
    """Retrieve Consul ACL token from /etc/consul.d/acl.hcl."""
    try:
        with open(CONSUL_ACL_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith('"agent" ='):
                    return line.split("=")[1].strip().strip('"')
    except FileNotFoundError:
        print("ACL file not found.")
    return None

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
            if isinstance(data, list) and len(data) > 0 and "Value" in data[0]:  # Ensure Value exists
                decoded_value = base64.b64decode(data[0]["Value"]).decode("utf-8")
                return json.loads(decoded_value)
        print("Error: Consul KV response does not contain a valid JSON value.")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Consul: {e}")
    return None

def get_s3_version_file():
    """Fetch or create an empty version file in S3 if not available."""
    version_key = f"{VERSION_FOLDER}version-{CURRENT_DATE}.json"

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=version_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Version file {version_key} not found in S3. Creating a new one.")
        empty_version = {"file": None, "timestamp": None}
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=version_key,
            Body=json.dumps(empty_version, indent=4),
            ContentType="application/json"
        )
        return empty_version

def get_s3_tracker(tracker_filename):
    """Fetch the corresponding tracker file from S3 (tracker-YYYY-MM-DD_CLUSTERID.json)."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=tracker_filename)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Tracker file {tracker_filename} not found in S3.")
        return None

def find_closest_version(tracker_data, target_time):
def find_closest_version(tracker_data, target_time):
    """Find the closest available journal version strictly before the target time."""
    target_dt = datetime.strptime(target_time, "%H:%M")

    # Filter versions that are strictly before target_time
    valid_versions = []
    for entry in tracker_data:
        timestamp = entry["timestamp"]
        entry_time = datetime.strptime(timestamp.split()[-1], "%H:%M:%S")

        if entry_time < target_dt:  # Only keep timestamps before HH:MM:00
            valid_versions.append((entry_time, entry))

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    # Sort by time and pick the latest available before target_time
    valid_versions.sort(reverse=True, key=lambda x: x[0])
    
    return valid_versions[0][1]  # Return the latest version before target_time


def get_latest_s3_journal(date):
    """Fetch the latest available journal for a given date from S3."""
    prefix = f"{JOURNAL_S3_PREFIX}{date}/"
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

    if "Contents" in response:
        latest_journal = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)[0]
        return latest_journal["Key"]
    else:
        print(f"No journal found for {date} in S3.")
        return None
        
def download_journal(s3_path, version_id=None):
    """Download a journal file from S3, using version ID if provided."""
    file_name = os.path.basename(s3_path)
    local_path = os.path.join(LOCAL_STORAGE, file_name)

    print(f"Downloading {file_name} from S3 path: {s3_path} (Version: {version_id})...")

    if version_id:
        s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path, ExtraArgs={"VersionId": version_id})
    else:
        s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path)

    print(f"Downloaded {file_name} to {local_path}")
    return local_path

def process_journal_sync():
    """Sync journals based on the Consul target version."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")

    # Fetch version file (create if missing)
    current_version = get_s3_version_file()
    current_version_date = current_version["file"].split("_")[-1].split(".")[0] if current_version["file"] else None

    if not current_version_date:
        print("No existing version in target. Pulling from start date.")
        current_version_date = target_version_date

    missing_journals = []

    # Get all full-day journals from `current_version_date` to `target_version_date - 1`
    current_date = datetime.strptime(current_version_date, "%Y-%m-%d")
    target_date = datetime.strptime(target_version_date, "%Y-%m-%d")

    while current_date < target_date:
        current_date += timedelta(days=1)
        s3_path = get_latest_s3_journal(current_date.strftime("%Y-%m-%d"))
        if s3_path:
            missing_journals.append((s3_path, None))

    # Fetch the closest timestamped version for `target_version_date`
    tracker_filename = f"{TRACKER_FOLDER}tracker-{target_version_date}_CLUSTERID.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if s3_tracker:
        closest_entry = find_closest_version(s3_tracker, target_version_time)
        if closest_entry:
            missing_journals.append((closest_entry["s3_path"], closest_entry["version_id"]))

    # Download and import missing journals
    for s3_path, version_id in missing_journals:
        file_name = os.path.basename(s3_path)
        print(f"Processing {file_name} (Version: {version_id})")

        downloaded_file = download_journal(s3_path, version_id)
        if trigger_import(downloaded_file):
            update_local_version(file_name)
        else:
            print(f"Import failed for {file_name} (Version {version_id}).")

if __name__ == "__main__":
    process_journal_sync()
