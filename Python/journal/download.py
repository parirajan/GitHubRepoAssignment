import os
import json
import boto3
import subprocess
import requests
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
CONSUL_ENDPOINT = "https://url:8501/v1/kv/journal/target_version_date_time"
CONSUL_ACL_FILE = "/etc/consul.d/acl.hcl"

# Get today's date for version tracking
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
LOCAL_VERSION_FILE = f"/path/to/version-{CURRENT_DATE}.json"

s3_client = boto3.client("s3")

import re

def get_consul_acl_token():
    """Retrieve Consul ACL token from /etc/consul.d/acl.hcl."""
    acl_file = "/etc/consul.d/acl.hcl"

    try:
        with open(acl_file, "r") as f:
            for line in f:
                # Strip spaces and check for the token assignment
                line = line.strip()
                match = re.search(r'"agent"\s*=\s*"([^"]+)"', line)
                if match:
                    return match.group(1)  # Extract and return the token
    except FileNotFoundError:
        print(f"ACL file not found at {acl_file}.")

    print("Error: Could not find ACL token in the file.")
    return None  # Return None if token is missing

def get_consul_target():
    """Fetch the target version from Consul KV using ACL authentication."""
    acl_token = get_consul_acl_token()
    if not acl_token:
        print("Error: No ACL token found.")
        return None

    headers = {"X-Consul-Token": acl_token}
    try:
        response = requests.get(CONSUL_ENDPOINT, headers=headers, verify=False)
        if response.status_code == 200:
            data = response.json()[0]["Value"]
            return json.loads(data)
        else:
            print(f"Error fetching Consul KV: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Consul: {e}")
        return None

def get_s3_tracker(tracker_filename):
    """Fetch the corresponding tracker file from S3 (tracker-YYYY-MM-DD.json)."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=tracker_filename)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Tracker file {tracker_filename} not found in S3.")
        return None

def list_s3_journals(date):
    """List all available journals for a given date in S3 (latest version)."""
    prefix = f"{JOURNAL_S3_PREFIX}{date}/"
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

    if "Contents" in response:
        return [obj["Key"] for obj in response["Contents"]]
    else:
        print(f"No journals found for {date} in S3.")
        return []

def get_latest_local_version():
    """Fetch the current local version file (if exists)."""
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            return json.load(f)
    return None

def download_journal(s3_key):
    """Download the latest version of a journal from S3."""
    file_name = os.path.basename(s3_key)
    local_path = os.path.join(LOCAL_STORAGE, file_name)

    print(f"Downloading {file_name} from {s3_key}...")
    s3_client.download_file(Bucket=S3_BUCKET, Key=s3_key, Filename=local_path)
    return local_path

def trigger_import(file_path):
    """Run the import process."""
    result = subprocess.run([IMPORT_SCRIPT, file_path], capture_output=True, text=True)
    return result.returncode == 0

def update_local_version(file_name):
    """Update local and S3 version file after successful import."""
    version_data = {"file": file_name, "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}

    # Save locally
    with open(LOCAL_VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=4)

    # Upload to S3 (overwrite previous version)
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=f"{VERSION_FOLDER}version-{CURRENT_DATE}.json",
        Body=json.dumps(version_data, indent=4),
        ContentType="application/json"
    )

    print(f"Updated local and S3 version file with {file_name}")

def fetch_missing_journals(target_version_date, target_version_time):
    """Determine missing journal files and fetch them from S3."""
    local_version = get_latest_local_version()
    current_version_date = local_version["file"].split("_")[-1].split(".")[0] if local_version else None

    missing_journals = []
    if current_version_date:
        current_date = datetime.strptime(current_version_date, "%Y-%m-%d")
        target_date = datetime.strptime(target_version_date, "%Y-%m-%d")

        # Process all full-day journals from (current_date + 1) to (target_date - 1)
        while current_date < target_date:
            current_date += timedelta(days=1)
            s3_journals = list_s3_journals(current_date.strftime("%Y-%m-%d"))
            missing_journals.extend(s3_journals)

    # Process the specific version for the target_date at the target_version_time
    tracker_filename = f"{TRACKER_FOLDER}tracker-{target_version_date}.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if not s3_tracker:
        print(f"Tracker file {tracker_filename} not found in S3.")
        return missing_journals

    # Find the correct version for the specified hour in the tracker
    for entry in s3_tracker:
        if entry["timestamp"].endswith(f"{target_version_time}:00:00"):
            missing_journals.append(entry["s3_path"])

    return missing_journals

def process_journal_sync():
    """Sync journals based on the Consul target version."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} AM")

    missing_journals = fetch_missing_journals(target_version_date, target_version_time)

    if not missing_journals:
        print("No new journals to download.")
        return

    # Download and import each missing journal
    for s3_key in missing_journals:
        downloaded_file = download_journal(s3_key)
        if trigger_import(downloaded_file):
            update_local_version(os.path.basename(s3_key))
        else:
            print(f"Import failed for {s3_key}.")

if __name__ == "__main__":
    process_journal_sync()
