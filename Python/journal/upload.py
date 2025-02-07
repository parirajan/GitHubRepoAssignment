import os
import json
import boto3
from datetime import datetime

# AWS S3 Configuration
S3_BUCKET = "your-bucket-name"
JOURNAL_DIR = "/path/to/journals"
CLUSTER_ID = "204"  # Source Cluster ID
TRACKER_FOLDER = "tracker/"  # S3 prefix for tracker files
JOURNAL_S3_PREFIX = "journals/"  # S3 prefix for journal files

s3_client = boto3.client("s3")

def get_tracker_filename():
    """Generate the tracker filename based on today's date and Source Cluster ID."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{TRACKER_FOLDER}tracker_{today}_{CLUSTER_ID}.json"

def fetch_tracker_from_s3(tracker_key):
    """Fetch the existing tracker file from S3 or create a new one if missing."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=tracker_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        print(f"Tracker file {tracker_key} not found. Creating a new one.")
        return []  # Return an empty list to initialize the tracker file

def upload_journal_to_s3(file_path, file_name):
    """Upload the journal file to S3 under a structured prefix and return the version ID."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Define S3 destination path (prefix + folder by date)
    s3_key = f"{JOURNAL_S3_PREFIX}{today_date}/{file_name}"

    s3_client.upload_file(file_path, S3_BUCKET, s3_key, ExtraArgs={"Metadata": {"timestamp": timestamp}})

    # Fetch latest version ID after upload
    version_info = s3_client.list_object_versions(Bucket=S3_BUCKET, Prefix=s3_key)
    latest_version = version_info.get("Versions", [])[0]
    version_id = latest_version["VersionId"]

    print(f"Uploaded {file_name} to S3 at {s3_key} with Version ID: {version_id}")
    return version_id, timestamp, s3_key

def rotate_tracker_file():
    """Ensure tracker file is rotated daily by checking if a new one needs to be created."""
    tracker_key = get_tracker_filename()
    
    # Check if today's tracker file exists, if not, create it
    existing_tracker = fetch_tracker_from_s3(tracker_key)
    if not existing_tracker:
        print(f"Creating a new tracker file for today: {tracker_key}")
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=tracker_key,
            Body=json.dumps([], indent=4),
            ContentType="application/json"
        )
    return tracker_key

def update_tracker(tracker_key, file_name, node_id, version_id, timestamp, s3_key):
    """Update the source tracker file in S3 with new version information."""
    tracker_data = fetch_tracker_from_s3(tracker_key)

    # Append new entry with correct file details and S3 path
    tracker_data.append({
        "timestamp": timestamp,
        "version_id": version_id,
        "file_name": file_name,
        "s3_path": s3_key,
        "node_id": node_id
    })

    # Upload updated tracker directly to S3
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=tracker_key,
        Body=json.dumps(tracker_data, indent=4),
        ContentType="application/json"
    )
    print(f"Updated S3 tracker file: {tracker_key}")

def process_journals():
    """Uploads the journal file to S3 every hour and updates the tracker."""
    today_date = datetime.now().strftime("%m-%d-%Y")
    tracker_key = rotate_tracker_file()  # Ensure the tracker file is rotated daily

    for file_name in os.listdir(JOURNAL_DIR):
        if file_name.startswith("journal_configuration_") and today_date in file_name:
            file_path = os.path.join(JOURNAL_DIR, file_name)

            # Extract Node ID from filename
            parts = file_name.split("_")
            node_id = parts[2]  # Extract Node ID from the journal file name

            # Step 1: Upload the journal file to S3 and retrieve version ID
            version_id, timestamp, s3_key = upload_journal_to_s3(file_path, file_name)

            # Step 2: Update the tracker with the uploaded file details
            update_tracker(tracker_key, file_name, node_id, version_id, timestamp, s3_key)

if __name__ == "__main__":
    process_journals()
