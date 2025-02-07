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

# Set the latest version file dynamically
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

def get_s3_tracker(tracker_filename):
    """Fetch the corresponding tracker file from S3 (tracker-YYYY-MM-DD_CLUSTERID.json)."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=tracker_filename)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Tracker file {tracker_filename} not found in S3.")
        return None

def find_closest_version(tracker_data, target_time):
    """Find the closest available journal version in the tracker."""
    target_dt = datetime.strptime(target_time, "%H:%M")
    available_versions = []

    for entry in tracker_data:
        timestamp = entry["timestamp"]
        entry_time = datetime.strptime(timestamp.split()[-1], "%H:%M:%S")
        available_versions.append((entry_time, entry))

    if not available_versions:
        print("No valid timestamps found in tracker.")
        return None

    # Sort available versions by time difference to find the closest one
    closest_version = min(available_versions, key=lambda x: abs(x[0] - target_dt))
    
    return closest_version[1]  # Return the closest entry

def download_journal(s3_path, version_id):
    """Download the closest available journal version from S3."""
    file_name = os.path.basename(s3_path)
    local_path = os.path.join(LOCAL_STORAGE, file_name)

    print(f"Downloading {file_name} (Version {version_id}) from {s3_path}...")

    s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path, ExtraArgs={"VersionId": version_id})

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

def process_journal_sync():
    """Sync journals based on the Consul target version."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")

    # Determine tracker filename
    tracker_filename = f"{TRACKER_FOLDER}tracker-{target_version_date}_CLUSTERID.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if not s3_tracker:
        print(f"Tracker file {tracker_filename} not found. Exiting.")
        return

    # Find closest available version
    closest_entry = find_closest_version(s3_tracker, target_version_time)

    if not closest_entry:
        print("No valid version found close to the target time.")
        return

    file_name = closest_entry["file_name"]
    version_id = closest_entry["version_id"]
    s3_path = closest_entry["s3_path"]
    node_id = closest_entry["node_id"]

    print(f"Closest available version found: {file_name} (Version ID: {version_id}, Node: {node_id})")

    # Download and import
    downloaded_file = download_journal(s3_path, version_id)
    if trigger_import(downloaded_file):
        update_local_version(file_name)
    else:
        print(f"Import failed for {file_name} (Version {version_id}).")

if __name__ == "__main__":
    process_journal_sync()
