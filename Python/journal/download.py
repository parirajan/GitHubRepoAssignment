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

def get_earliest_s3_journal():
    """Fetch the earliest available journal in S3 (start of time)."""
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=JOURNAL_S3_PREFIX)

    if "Contents" in response:
        earliest_journal = sorted(response["Contents"], key=lambda x: x["LastModified"])[0]
        print(f"Earliest available journal found: {earliest_journal['Key']}")
        return earliest_journal["Key"]
    else:
        print("No journal files found in S3.")
        return None

def find_closest_version(tracker_data, target_time):
    """Find the closest available journal version strictly before the target time."""
    target_dt = datetime.strptime(target_time, "%H:%M")
    valid_versions = []

    for entry in tracker_data:
        timestamp = entry["timestamp"]
        entry_time = datetime.strptime(timestamp.split()[-1], "%H:%M:%S")

        if entry_time < target_dt:  # Only keep timestamps before HH:MM:00
            valid_versions.append((entry_time, entry))

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    valid_versions.sort(reverse=True, key=lambda x: x[0])
    return valid_versions[0][1]  # Return the latest version before target_time

def download_journal(s3_path, version_id=None):
    """Download a journal file from S3, using version ID if provided."""
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
        
def update_local_version(file_name):
    """Update local and S3 version file after successful import."""
    version_data = {
        "file": file_name,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save the updated version locally
    with open(LOCAL_VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=4)

    # Upload the updated version file to S3
    version_key = f"{VERSION_FOLDER}version-{CURRENT_DATE}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=version_key,
        Body=json.dumps(version_data, indent=4),
        ContentType="application/json"
    )

    print(f"Updated local and S3 version file: {file_name} at {version_data['timestamp']}")

def get_s3_status_file():
    """Fetch the latest status.json from S3 before processing."""
    status_key = f"{VERSION_FOLDER}status.json"
    local_status_file = "/path/to/status.json"

    try:
        s3_client.download_file(Bucket=S3_BUCKET, Key=status_key, Filename=local_status_file)
        print(f"Pulled latest status.json from S3: {local_status_file}")
        return True
    except s3_client.exceptions.NoSuchKey:
        print(f"ERROR: status.json not found in S3. Import cannot proceed.")
        return False


def upload_s3_status_file():
    """Upload the locally updated status.json back to S3 after import."""
    status_key = f"{VERSION_FOLDER}status.json"
    local_status_file = "/path/to/status.json"

    if not os.path.exists(local_status_file):
        print(f"ERROR: Local status.json missing after import. Possible corruption detected.")
        return False

    # Upload updated status.json to S3
    s3_client.upload_file(Filename=local_status_file, Bucket=S3_BUCKET, Key=status_key)
    print(f"Uploaded updated status.json to S3.")
    return True




def process_journal_sync():
    """Sync journals based on the Consul target version."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")
    
    #Ensure status.json is available before proceeding
    if not get_s3_status_file():
        print("ERROR: status.json is missing. Import cannot proceed.")
        return  # Stop execution if status.json is not available
    
    current_version = get_s3_version_file()
    current_version_date = current_version["file"].split("_")[-1].split(".")[0] if current_version["file"] else None

    if not current_version_date:
        print("No previous version found. Fetching earliest available journal.")
        s3_path = get_earliest_s3_journal()
        if s3_path:
            current_version_date = s3_path.split("_")[-1].split(".")[0]
        else:
            print("No journals found in S3, cannot proceed.")
            return
            
    #NEW CHECK: Stop if requested version is older than the current running version
    if current_version_date:
        if target_version_date < current_version_date:
            print(
                f"ERROR: Requested version {target_version_date} is older than the current running version {current_version_date}. Aborting import."
            )
            return

    missing_journals = []
    current_date = datetime.strptime(current_version_date, "%Y-%m-%d")
    target_date = datetime.strptime(target_version_date, "%Y-%m-%d")

    while current_date < target_date:
        current_date += timedelta(days=1)
        s3_path = get_earliest_s3_journal()
        if s3_path:
            missing_journals.append((s3_path, None))

    tracker_filename = f"{TRACKER_FOLDER}tracker-{target_version_date}_source-cluster-204.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if s3_tracker:
        closest_entry = find_closest_version(s3_tracker, target_version_time)
        if closest_entry:
            missing_journals.append((closest_entry["s3_path"], closest_entry["version_id"]))

    for s3_path, version_id in missing_journals:
        downloaded_file = download_journal(s3_path, version_id)
        if downloaded_file:
            print(f"Importing {downloaded_file}...")
            update_local_version(downloaded_file)
            #Ensure status.json is uploaded after import
            if not upload_s3_status_file():
                print("⛔ ERROR: status.json upload failed. System state may be corrupted.")
                return  # Stop execution if status.json upload fails

if __name__ == "__main__":
    process_journal_sync()
