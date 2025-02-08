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
LOCAL_STATUS_FILE = "/path/to/status.json"

def run_import_script(file_path):
    """Runs the compiled Python import script with the downloaded file."""
    script_dir = os.path.dirname(IMPORT_SCRIPT)  # Get the directory of run.pyc
    command = ["python", IMPORT_SCRIPT, file_path]  # Run with Python

    try:
        result = subprocess.run(command, cwd=script_dir, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Import script ran successfully for {file_path}.")
            return True
        else:
            print(f"⛔ ERROR: Import script failed for {file_path}.\n{result.stderr}")
            return False
    except Exception as e:
        print(f"⛔ ERROR: Failed to execute import script: {e}")
        return False



def get_s3_status_file():
    """Check if status.json exists in S3. If missing, continue execution."""
    status_key = f"{VERSION_FOLDER}status.json"

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=status_key)
        print(f"✅ status.json found in S3.")
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(f"⚠️ WARNING: {status_key} not found in S3. Continuing execution.")
            return False  # Continue execution
        else:
            print(f"⛔ ERROR: Unexpected S3 error checking status.json - {str(e)}")
            return False



def get_s3_status_file():
    """Check if status.json exists in S3. If missing, allow execution to continue (Day 0 handling)."""
    status_key = f"{VERSION_FOLDER}status.json"

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=status_key)
        print(f"✅ status.json found in S3.")
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(f"⚠️ WARNING: {status_key} not found in S3 (Day 0). Continuing execution.")
            return False  # Allow execution to continue
        else:
            print(f"⛔ ERROR: Unexpected S3 error checking status.json - {str(e)}")
            return False



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
    """Find the closest available journal version strictly before the target time."""
    target_dt = datetime.strptime(target_time, "%H:%M")
    valid_versions = []

    for entry in tracker_data:
        timestamp = entry["timestamp"]
        entry_time = datetime.strptime(timestamp.split()[-1], "%H:%M:%S")

        if entry_time < target_dt:
            valid_versions.append((entry_time, entry))

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    valid_versions.sort(reverse=True, key=lambda x: x[0])
    return valid_versions[0][1]


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


def process_journal_sync():
    """Sync journals based on the Consul target version, enforcing strict import order."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("⛔ ERROR: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"📌 Target version date: {target_version_date} at {target_version_time} HH:MM")

    # Check if status.json exists in S3
    status_exists = get_s3_status_file()
    
    # Allow execution on Day 0 if status.json is missing
    if not status_exists:
        print("⚠️ status.json is missing (Day 0). Allowing first import to proceed.")


    # Fetch current version from S3
    current_version = get_s3_version_file()
    current_version_date = (
        current_version["file"].split("_")[-1].split(".")[0]
        if current_version["file"]
        else None
    )

    if current_version_date:
        if target_version_date < current_version_date:
            print(f"⛔ ERROR: Requested version {target_version_date} is older than the current running version {current_version_date}. Aborting import.")
            return

    missing_journals = []

    tracker_filename = f"{TRACKER_FOLDER}tracker-{target_version_date}_source-cluster-204.json"
    s3_tracker = get_s3_tracker(tracker_filename)

    if s3_tracker:
        closest_entry = find_closest_version(s3_tracker, target_version_time)
        if closest_entry:
            missing_journals.append((closest_entry["s3_path"], closest_entry["version_id"]))

    for s3_path, version_id in missing_journals:
        downloaded_file = download_journal(s3_path, version_id)
        if downloaded_file:
            print(f"📌 Importing {downloaded_file}...")
            if trigger_import(downloaded_file):
                update_local_version(downloaded_file)  # ✅ Update version.json

                # Ensure status.json is uploaded after import
                if not upload_s3_status_file():
                    print("⛔ ERROR: status.json upload failed. System state may be corrupted.")
                    return


if __name__ == "__main__":
    process_journal_sync()
