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

        if entry_time < target_dt:
            valid_versions.append((entry_time, entry))

    if not valid_versions:
        print(f"No versions found strictly before {target_time}.")
        return None

    valid_versions.sort(reverse=True, key=lambda x: x[0])
    return valid_versions[0][1]


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
    """Sync journals based on the Consul target version."""
    target_version_info = get_consul_target()
    if not target_version_info:
        print("Error: Could not retrieve target version from Consul.")
        return

    target_version_date = target_version_info["date"]
    target_version_time = target_version_info["time"]

    print(f"Target version date: {target_version_date} at {target_version_time} HH:MM")

    current_version = get_s3_version_file()
    if current_version and current_version.get("file"):
        current_version_date = current_version["file"].split("_")[-1].split(".")[0]
    else:
        current_version_date = None

    missing_journals = []

    if not current_version_date:
        earliest_s3_path = get_earliest_s3_journal()
        if earliest_s3_path:
            current_version_date = earliest_s3_path.split("_")[-1].split(".")[0]
            missing_journals.append((earliest_s3_path, None))

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

    print("Journal sync and import process completed successfully.")
