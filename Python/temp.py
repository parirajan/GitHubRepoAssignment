import os
import time
import datetime
import hashlib
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Lock, Timer

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the folder to watch
FOLDER_TO_WATCH = "/path/to/watch/folder"
WAIT_TIME_SECONDS = 5  # Wait for 5 seconds to ensure the file is complete
COOLDOWN_TIME_SECONDS = 10  # Debounce period to avoid multiple uploads
TEMP_EXTENSIONS = ['.swp', '.swx', '.part', '.~']  # Temporary file extensions

# GitLab project and API details (use environment variables for security)
GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "your_project_id")
GITLAB_PACKAGE_REGISTRY_URL = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/packages/generic/package_name/version"
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN", "your_trigger_token")
GITLAB_REF = os.getenv("GITLAB_REF", "main")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", "your_access_token")

# Keep track of files that have already been uploaded to avoid duplicate uploads
uploaded_files = set()
processing_files_lock = Lock()

# To debounce file events and prevent reprocessing within the cooldown period
file_event_timestamps = {}

class IrisFileHandler(FileSystemEventHandler):
    def process(self, event):
        file_path = event.src_path
        file_name, file_extension = os.path.splitext(file_path)

        # Ignore temporary files
        if any(file_extension.endswith(ext) for ext in TEMP_EXTENSIONS):
            logging.info(f"Ignored temporary file: {file_path}")
            return

        # Log all events
        logging.info(f"Detected event '{event.event_type}' for {file_path}")

        # Only process the file if it's a .iris file and if the event is 'modified'
        if file_extension == '.iris' and event.event_type == 'modified':
            self.schedule_upload(file_path)

    def schedule_upload(self, file_path):
        """
        Schedule the file upload with a cooldown period to debounce multiple events.
        """
        now = time.time()

        # Debounce logic: wait for COOLDOWN_TIME_SECONDS before processing the file again
        if file_path in file_event_timestamps:
            last_event_time = file_event_timestamps[file_path]
            if now - last_event_time < COOLDOWN_TIME_SECONDS:
                logging.info(f"Skipping file {file_path} due to cooldown period.")
                return

        file_event_timestamps[file_path] = now

        # Wait for the file to stabilize and then process it
        Timer(WAIT_TIME_SECONDS, self.handle_iris_file, [file_path]).start()

    def handle_iris_file(self, file_path):
        # Lock to avoid race conditions on processing files
        with processing_files_lock:
            # Ensure the file is uploaded only once
            if file_path in uploaded_files:
                logging.info(f"File {file_path} has already been uploaded. Skipping.")
                return
            else:
                logging.info(f"Processing file {file_path} for upload.")
                uploaded_files.add(file_path)

        # Ensure the file is stable (wait for size to stabilize)
        if not self.is_file_stable(file_path):
            logging.info(f"File {file_path} is still being modified.")
            return

        # Create a checksum file (but don't upload it to the package registry)
        checksum_file_path = self.create_checksum_file(file_path)

        # Create a folder in the GitLab package registry with the current date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        package_folder = f"{GITLAB_PACKAGE_REGISTRY_URL}/{current_date}"

        # Upload only the .iris file to GitLab package registry (no metadata files)
        self.upload_to_gitlab(file_path, package_folder)

        # Store the checksum file locally (as a GitLab artifact)
        logging.info(f"Checksum file stored at: {checksum_file_path}")

        # Trigger GitLab pipeline to validate the file and checksum
        self.trigger_gitlab_pipeline(file_path, checksum_file_path)

    def is_file_stable(self, file_path):
        """
        Check if the file size has remained stable for WAIT_TIME_SECONDS.
        """
        previous_size = os.path.getsize(file_path)
        time.sleep(WAIT_TIME_SECONDS)
        current_size = os.path.getsize(file_path)

        return previous_size == current_size

    def create_checksum_file(self, file_path):
        """
        Create a .cksum file containing the checksum, timestamp, and filename.
        """
        file_checksum = self.calculate_checksum(file_path)
        file_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        file_name = os.path.basename(file_path)

        # Create the .cksum file path (same location as .iris file but with .cksum extension)
        checksum_file_path = f"{file_path}.cksum"
        
        with open(checksum_file_path, "w") as f:
            f.write(f"File: {file_name}\n")
            f.write(f"Checksum: {file_checksum}\n")
            f.write(f"Timestamp: {file_timestamp}\n")

        logging.info(f"Checksum file created at: {checksum_file_path}")
        return checksum_file_path

    def calculate_checksum(self, file_path):
        """
        Calculate the SHA-256 checksum of the file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        logging.info(f"Checksum for {file_path}: {checksum}")
        return checksum

    def upload_to_gitlab(self, file_path, package_folder):
        """
        Upload the file to GitLab Package Registry.
        """
        headers = {
            "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN
        }
        file_name = os.path.basename(file_path)
        upload_url = f"{package_folder}/{file_name}"

        with open(file_path, 'rb') as file_data:
            response = requests.put(upload_url, headers=headers, data=file_data)

        if response.status_code == 201:
            logging.info(f"File {file_name} successfully uploaded to GitLab package registry.")
        else:
            logging.error(f"Failed to upload {file_name}. Response: {response.content}")

    def trigger_gitlab_pipeline(self, file_path, checksum_file_path):
        """
        Trigger a GitLab pipeline to validate the uploaded file and checksum.
        """
        url = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
        file_name = os.path.basename(file_path)
        checksum_file_name = os.path.basename(checksum_file_path)
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "token": GITLAB_TRIGGER_TOKEN,
            "ref": GITLAB_REF,
            "variables": {
                "UPLOADED_FILE": file_name,
                "CHECKSUM_FILE": checksum_file_name
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            logging.info(f"GitLab pipeline successfully triggered for {file_name}.")
        else:
            logging.error(f"Failed to trigger GitLab pipeline for {file_name}. Response: {response.content}")

    def on_created(self, event):
        self.process(event)

    def on_modified(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def on_deleted(self, event):
        logging.info(f"File {event.src_path} deleted.")

if __name__ == "__main__":
    event_handler = IrisFileHandler()
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
