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



def get_consul_acl_token():
    """Retrieve the Consul ACL token from the ACL configuration file."""
    acl_file = CONSUL_ACL_FILE

    try:
        with open(acl_file, "r") as f:
            for line in f:
                line = line.strip()
                match = re.search(r'agent\s*=\s*"([^"]+)"', line)
                if match:
                    return match.group(1)
    except FileNotFoundError:
        print(f"ACL file not found at {acl_file}.")
    
    print("Error: Could not find ACL token in the file.")
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
            if isinstance(data, list) and len(data) > 0 and "Value" in data[0]:
                decoded_value = base64.b64decode(data[0]["Value"]).decode("utf-8")
                return json.loads(decoded_value)

            print("Error: Consul KV response does not contain a valid JSON value.")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Consul: {e}")

    return None


def get_s3_version_file():
    """Fetch the latest version.json from S3, or create a new one if missing."""
    version_key = f"{VERSION_FOLDER}version.json"  # Ensure single version file

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=version_key)
        version_data = json.loads(response["Body"].read().decode("utf-8"))

        if not isinstance(version_data, list):  # Ensure it’s a list
            print("WARNING: version.json is corrupted. Resetting to an empty list.")
            version_data = []

    except s3_client.exceptions.NoSuchKey:
        print("version.json not found in S3. Creating a new one.")
        version_data = []  # Start fresh

    return version_data


def update_local_version(file_name, s3_version_id=None):
    """Update version.json after successful import, keeping only the last 50 entries."""
    version_key = f"{VERSION_FOLDER}version.json"
    version_data = get_s3_version_file()  # Fetch latest data

    # Debugging: Print received values before updating
    print(f"Updating version.json with File: {file_name}, S3 Version ID: {s3_version_id}")

    # Ensure version_id is correct
    if not s3_version_id or s3_version_id == "N/A":
        print(f"WARNING: S3 Version ID is missing for {file_name}. This should not happen!")
    
    # Create a new version entry
    new_entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "file": file_name,
        "s3_version_id": s3_version_id if s3_version_id else "N/A"  # Handle missing version_id
    }

    # Append the new entry
    version_data.append(new_entry)

    # Keep only the last 50 entries
    if len(version_data) > 50:
        version_data = version_data[-50:]

    # Save locally before uploading
    with open(LOCAL_VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=4)

    # Upload updated version.json to S3
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=version_key,
        Body=json.dumps(version_data, indent=4),
        ContentType="application/json"
    )

    print(f"SUCCESS: Updated version.json in S3 with {file_name} and S3 Version ID: {s3_version_id}")

def get_s3_tracker(tracker_filename):
    """Fetch the corresponding tracker file from S3."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=f"{TRACKER_FOLDER}{tracker_filename}")
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Tracker file {tracker_filename} not found in S3.")
        return None


def get_earliest_s3_journal():
    """Fetch the earliest available journal in S3."""
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=JOURNAL_S3_PREFIX)

    if "Contents" in response:
        earliest_journal = sorted(response["Contents"], key=lambda x: x["LastModified"])[0]
        print(f"Earliest available journal found: {earliest_journal['Key']}")
        return earliest_journal["Key"]
    else:
        print("No journal files found in S3.")
        return None


def get_latest_s3_journal(date):
    """Fetch the latest available journal in S3 for a given date."""
    prefix = f"{JOURNAL_S3_PREFIX}{date}/"
    print(f"DEBUG: Looking for journal files in S3 with prefix: {prefix}")

    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

    if "Contents" in response:
        latest_journal = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)[0]
        print(f"Latest available journal found: {latest_journal['Key']}")
        return latest_journal["Key"]
    else:
        print(f"No journal files found for {date} in S3.")
        return None


def find_closest_version(tracker_data, target_time):
    """Find the closest available journal version strictly before the target time."""
    target_dt = datetime.strptime(target_time, "%H:%M")
    valid_versions = []

    for entry in tracker_data:
        timestamp = entry["timestamp"]
        entry_time = datetime.strptime(timestamp.split()[-1], "%H:%M:%S")

        if entry_time < target_dt:  # Only pick timestamps before the target time
            valid_versions.append((entry_time, entry))

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    valid_versions.sort(reverse=True, key=lambda x: x[0])  # Sort descending by time
    selected_entry = valid_versions[0][1]  # Select the latest valid entry

    # Debugging: Print the selected version
    print(f"Closest Version Selected: {selected_entry['version_id']} at {selected_entry['timestamp']}")
    return selected_entry  # Return full entry including `version_id`


def download_journal(s3_path, version_id):
    """Download a journal file from S3."""
    if not s3_path:
        print("Error: S3 path is None, skipping download.")
        return None

    file_name = os.path.basename(s3_path)
    local_path = os.path.join(LOCAL_STORAGE, file_name)

    print(f"Downloading {file_name} from S3 path: {s3_path} (Version: {version_id})...")

    try:
        if version_id:
            s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path, ExtraArgs={"VersionId": version_id})
        else:
            s3_client.download_file(Bucket=S3_BUCKET, Key=s3_path, Filename=local_path)

        print(f"Downloaded {file_name} to {local_path}")
        return local_path
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")
        return None


def process_journal_sync():
    """Sync journals based on the target version from Consul and manage versioning."""
    
    # Step 1: Retrieve the target version from Consul KV
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")

    # Step 2: Fetch the latest status.json from S3 **before proceeding**
    if not get_s3_status_file():
        print("ERROR: status.json is missing or corrupted. Aborting import.")
        return  # Stop execution if status.json is not found or is invalid

    # Step 3: Fetch the latest version.json from S3
    s3_version_data = get_s3_version_file()
    
    # Step 4: Check if a local version.json exists
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            local_version_data = json.load(f)
    else:
        local_version_data = None

    # Step 5: If S3 version is missing (Day 0), allow first import
    if not s3_version_data and not local_version_data:
        print("No previous version found in S3 or locally. Allowing first import.")
        current_version_date = None  # Proceed with importing from the beginning

    # Step 6: If both exist, check for corruption (S3 should not be behind local)
    elif s3_version_data and local_version_data:
        s3_latest_timestamp = s3_version_data[-1]["timestamp"]
        local_latest_timestamp = local_version_data[-1]["timestamp"]

        if s3_latest_timestamp < local_latest_timestamp:
            print("ERROR: S3 version.json is older than the local version. Manual intervention required.")
            return  # Stop execution

    # Step 7: Determine the current version date
    if s3_version_data:
        current_version_date = s3_version_data[-1]["file"].split("_")[-1].split(".")[0]  # Extract date from filename
    else:
        current_version_date = None

    missing_journals = []

    # Step 8: If no previous version, start with the earliest journal available in S3
    if not current_version_date:
        earliest_s3_path = get_earliest_s3_journal()
        if earliest_s3_path:
            current_version_date = earliest_s3_path.split("_")[-1].split(".")[0]
            missing_journals.append((earliest_s3_path, None))

    # Step 9: Loop through missing journal files from current_version_date → target_version_date
    current_date = datetime.strptime(current_version_date, "%Y-%m-%d") if current_version_date else None
    target_date = datetime.strptime(target_version_date, "%Y-%m-%d")

    while current_date and current_date < target_date:
        s3_path = get_latest_s3_journal(current_date.strftime("%Y-%m-%d"))
        if s3_path:
            missing_journals.append((s3_path, None))
        current_date += timedelta(days=1)

    # Step 10: Fetch the closest version from tracker
    tracker_filename = f"tracker_{target_version_date}_{source_cluster_id}.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    # Ensure closest_entry is always defined
    closest_entry = None

    if s3_tracker:
        closest_entry = find_closest_version(s3_tracker, target_version_time)
        if closest_entry:
            missing_journals.append((closest_entry["s3_path"], closest_entry["version_id"]))

# Step 11: Download missing journals & capture the correct `s3_version_id`
downloaded_files = []
journal_version_map = {}  # Store mapping of file name → version ID

for s3_path, version_id in missing_journals:
    if s3_path:
        local_file = download_journal(s3_path, version_id)
        if local_file:
            downloaded_files.append(local_file)
            journal_version_map[local_file] = version_id  # Map file → version_id

# Debugging: Print downloaded files and their S3 version IDs
print("DEBUG: Downloaded files and their S3 version IDs:")
for file, version in journal_version_map.items():
    print(f" - {file}: Version ID {version}")

# Ensure import runs once for all files
if downloaded_files:
    print(f"Importing batch of {len(downloaded_files)} files...")

    if run_import_script(downloaded_files):  # Run import once
        for downloaded_file in downloaded_files:
            # Pass correct version_id
            update_local_version(downloaded_file, journal_version_map.get(downloaded_file, "N/A"))
        
        # Upload status.json after import
        if not upload_s3_status_file():
            print("ERROR: status.json upload failed. System state may be corrupted.")
            return

    # Step 12: Run import job and update version.json **only after successful import**
    if downloaded_files:
        print(f"Importing batch of {len(downloaded_files)} files...")

        if run_import_script(downloaded_files):  # Only update version.json if import succeeds
            # Step 12.1: Upload status.json to S3 **after successful import**
            if not upload_s3_status_file():
                print("WARNING: Failed to upload status.json to S3. Manual check required.")

            # Step 12.2: Update version.json after a successful import
            for downloaded_file in downloaded_files:
                update_local_version(downloaded_file, journal_version_map.get(downloaded_file, None))

    print("Journal sync and import process completed successfully.")
