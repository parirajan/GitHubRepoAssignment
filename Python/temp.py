import time
import hashlib
import os
import datetime
import requests
import tempfile
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Lock
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the folder to watch
FOLDER_TO_WATCH = "/path/to/watch/folder"
WAIT_TIME_SECONDS = 5  # Wait for 5 seconds to ensure the file is complete
COOLDOWN_TIME_SECONDS = 60  # Prevent file reprocessing for 60 seconds after processing

# GitLab project and API details (use environment variables for security)
GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "your_project_id")
GITLAB_PACKAGE_REGISTRY_URL = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/packages/generic/package_name/version"  # Replace 'package_name' and 'version'
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN", "your_trigger_token")
GITLAB_REF = os.getenv("GITLAB_REF", "main")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", "your_access_token")

# Define file extensions and hidden files to ignore (including .swp, .tmp, hidden files)
IGNORE_EXTENSIONS = ['.swp', '.tmp', '.part', '.~', '.swx']
HIDDEN_FILE_PREFIX = '.'  # Ignore files starting with a dot (e.g., .swp files)

# Keep track of files that are currently being processed (thread-safe)
processing_files = set()
processing_files_lock = Lock()

# Keep track of files that are currently being uploaded
currently_uploading = set()

# To debounce file events and prevent reprocessing within cooldown period
file_event_timestamps = {}

class Watcher:
    def __init__(self, folder_to_watch):
        self.folder_to_watch = folder_to_watch
        self.event_handler = Handler()
        self.observer = Observer()

    def run(self):
        self.observer.schedule(self.event_handler, self.folder_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    def process(self, event):
        """
        Process any changes in the directory (file modifications, creation, etc.)
        """
        file_path = event.src_path

        # Ignore hidden files and certain temporary file extensions
        _, file_extension = os.path.splitext(file_path)
        if file_extension in IGNORE_EXTENSIONS or os.path.basename(file_path).startswith(HIDDEN_FILE_PREFIX):
            logging.info(f"Ignored temporary/hidden file: {file_path}")
            return

        event_type = event.event_type

        # Debounce and avoid reprocessing the same file within the cooldown period
        now = time.time()
        if file_path in file_event_timestamps:
            last_event_time = file_event_timestamps[file_path]
            if now - last_event_time < COOLDOWN_TIME_SECONDS:  # Cooldown period
                logging.info(f"Skipping file {file_path} (event: {event_type}) due to cooldown.")
                return

        file_event_timestamps[file_path] = now

        # Avoid re-processing the same file if it's already being uploaded
        with processing_files_lock:
            if file_path in currently_uploading:
                logging.info(f"File {file_path} is already being uploaded, skipping (event: {event_type}).")
                return
            currently_uploading.add(file_path)

        logging.info(f"Processing file {file_path} due to event: {event_type}")

        if event.event_type in ("created", "modified"):
            try:
                # Log the event details (modification time, file size)
                self.log_event_details(event, file_path)

                # 1. Ensure the file is stable for more than WAIT_TIME_SECONDS
                if not self.is_file_stable(file_path):
                    logging.info(f"File {file_path} is still being modified, skipping.")
                    return

                # 2. Create metadata without modifying the original file
                file_checksum = self.calculate_checksum(file_path)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metadata_file_path = self.create_metadata_file(file_path, file_checksum, timestamp)

                # 3. Upload the original file and metadata file once
                self.upload_to_package_registry(file_path, metadata_file_path)

                # 4. Trigger the GitLab pipeline to validate the uploaded file and metadata
                self.trigger_gitlab_pipeline(file_path, metadata_file_path)

            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
            finally:
                # Ensure that the file is removed from the currently_uploading set even on error
                with processing_files_lock:
                    currently_uploading.remove(file_path)

    def is_file_stable(self, file_path):
        """
        Check if a file has not been modified for the past WAIT_TIME_SECONDS,
        and if its size remains stable for two consecutive checks.
        """
        initial_mod_time = os.path.getmtime(file_path)
        initial_size = os.path.getsize(file_path)

        # Wait for stability
        time.sleep(WAIT_TIME_SECONDS)

        current_mod_time = os.path.getmtime(file_path)
        current_size = os.path.getsize(file_path)

        # File is stable if modification time and size have not changed
        return (initial_mod_time == current_mod_time) and (initial_size == current_size)

    def log_event_details(self, event, file_path):
        """
        Log file event details including event type, file size, and modification time.
        """
        mod_time = os.path.getmtime(file_path)
        file_size = os.path.getsize(file_path)
        logging.info(f"Event: {event.event_type}, File: {file_path}, "
                     f"ModTime: {mod_time}, Size: {file_size}, Timestamp: {datetime.datetime.now()}")

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

    def create_metadata_file(self, file_path, checksum, timestamp):
        """
        Create a metadata file in a temporary directory outside the watched folder.
        """
        metadata_file_name = f"{os.path.basename(file_path)}.metadata.txt"
        
        # Create a temporary directory for the metadata file outside the watched folder
        temp_dir = tempfile.gettempdir()  # Use any non-watched directory
        metadata_file_path = os.path.join(temp_dir, metadata_file_name)
        
        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write(f"File: {os.path.basename(file_path)}\n")
            metadata_file.write(f"Checksum (SHA-256): {checksum}\n")
            metadata_file.write(f"Timestamp: {timestamp}\n")

        logging.info(f"Metadata file created at: {metadata_file_path}")
        return metadata_file_path

    def upload_to_package_registry(self, file_path, metadata_file_path):
        """
        Upload the original file and metadata file to GitLab Package Registry using the GitLab API.
        """
        headers = {
            "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN
        }

        session = self._get_retry_session()

        try:
            # Upload the original file (only once, without modifying its contents)
            with open(file_path, 'rb') as file_data:
                file_name = os.path.basename(file_path)
                response = session.put(
                    f"{GITLAB_PACKAGE_REGISTRY_URL}/{file_name}",
                    headers=headers,
                    data=file_data,
                    timeout=10,
                    verify=False  # Suppress TLS verification for now
                )

                if response.status_code == 201:
                    logging.info(f"File {file_name} uploaded to GitLab Package Registry.")
                else:
                    logging.error(f"Failed to upload {file_name} to Package Registry. Status Code: {response.status_code}, Response: {response.content}")

            # Upload the metadata file
            with open(metadata_file_path, 'rb') as metadata_data:
                metadata_file_name = os.path.basename(metadata_file_path)
                response = session.put(
                    f"{GITLAB_PACKAGE_REGISTRY_URL}/{metadata_file_name}",
                    headers=headers,
                    data=metadata_data,
                    timeout=10,
                    verify=False  # Suppress TLS verification for now
                )

                if response.status_code == 201:
                    logging.info(f"Metadata file {metadata_file_name} uploaded to GitLab Package Registry.")

                    # Delete the metadata file after successful upload
                    try:
                        os.remove(metadata_file_path)
                        logging.info(f"Metadata file {metadata_file_path} deleted from source.")
                    except OSError as e:
                        logging.error(f"Error deleting metadata file: {e}")
                else:
                    logging.error(f"Failed to upload {metadata_file_name} to Package Registry. Status Code: {response.status_code}, Response: {response.content}")
        
        except Exception as e:
            logging.error(f"Exception during file upload: {e}")

    def trigger_gitlab_pipeline(self, file_path, metadata_file_path):
        """
        Trigger a GitLab CI/CD pipeline to validate the uploaded file and metadata using the GitLab API.
        Pass the uploaded file name and metadata file name as variables.
        """
        url = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "token": GITLAB_TRIGGER_TOKEN,
            "ref": GITLAB_REF,
            "variables": {
                "UPLOADED_FILE": os.path.basename(file_path),  # Pass the uploaded file as a variable
                "METADATA_FILE": os.path.basename(metadata_file_path)  # Pass the metadata file as a variable
            }
        }

        session = self._get_retry_session()

        try:
            response = session.post(url, headers=headers, json=payload, timeout=10, verify=False)  # Suppress TLS verification

            if response.status_code == 201:
                logging.info(f"GitLab pipeline triggered successfully for {file_path}")
            else:
                logging.error(f"Failed to trigger GitLab pipeline. Status Code: {response.status_code}, Response: {response.content}")
        except Exception as e:
            logging.error(f"Error triggering GitLab pipeline for {file_path}: {e}")

    def _get_retry_session(self):
        """
        Create a requests session with retry logic and backoff.
        """
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        return session

    def on_modified(self, event):
        # Process only "modified" event once, skip if already processed on "created"
        self.process(event)

    def on_created(self, event):
        # Process only "created" event once, skip if already processed on "modified"
        self.process(event)

if __name__ == "__main__":
    watcher = Watcher(FOLDER_TO_WATCH)
    watcher.run()
