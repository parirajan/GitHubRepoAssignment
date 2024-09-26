import time
import hashlib
import os
import datetime
import requests
import tempfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the folder to watch
FOLDER_TO_WATCH = "/path/to/watch/folder"

# GitLab project and API details
GITLAB_API_URL = "https://gitlab.com/api/v4"
GITLAB_PROJECT_ID = "your_project_id"
GITLAB_PACKAGE_REGISTRY_URL = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/packages/generic/package_name/version"  # Replace 'package_name' and 'version'
GITLAB_TRIGGER_TOKEN = "your_trigger_token"
GITLAB_REF = "main"  # Branch to run the job on
GITLAB_PERSONAL_ACCESS_TOKEN = "your_access_token"  # For file upload

# Define file extensions to ignore (e.g., swap files, temporary files)
IGNORE_EXTENSIONS = ['.swp', '.tmp', '.part', '.~', '.swx']

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

        # Check if the file is a swap/temporary file and ignore it if necessary
        _, file_extension = os.path.splitext(file_path)
        if file_extension in IGNORE_EXTENSIONS:
            print(f"Ignored temporary/swap file: {file_path}")
            return

        if event.event_type in ("modified", "created") and not event.is_directory:
            # 1. Create metadata without modifying the original file
            file_checksum = self.calculate_checksum(file_path)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata_file_path = self.create_metadata_file(file_path, file_checksum, timestamp)

            # 2. Upload the original file and metadata file once
            self.upload_to_package_registry(file_path, metadata_file_path)

            # 3. Trigger the GitLab pipeline to validate the uploaded file and metadata
            self.trigger_gitlab_pipeline(file_path, metadata_file_path)

    def calculate_checksum(self, file_path):
        """
        Calculate the SHA-256 checksum of the file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        print(f"Checksum for {file_path}: {checksum}")
        return checksum

    def create_metadata_file(self, file_path, checksum, timestamp):
        """
        Create a metadata file in a temporary directory outside the watched folder.
        """
        metadata_file_name = f"{os.path.basename(file_path)}.metadata.txt"
        
        # Create a temporary directory for the metadata file outside the watched folder
        temp_dir = "/tmp"  # You can use any non-watched directory here
        metadata_file_path = os.path.join(temp_dir, metadata_file_name)
        
        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write(f"File: {os.path.basename(file_path)}\n")
            metadata_file.write(f"Checksum (SHA-256): {checksum}\n")
            metadata_file.write(f"Timestamp: {timestamp}\n")

        print(f"Metadata file created at: {metadata_file_path}")
        return metadata_file_path

    def upload_to_package_registry(self, file_path, metadata_file_path):
        """
        Upload the original file and metadata file to GitLab Package Registry using the GitLab API.
        Ensure that the original file is only uploaded once.
        """
        headers = {
            "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN
        }

        # Upload the original file (only once)
        with open(file_path, 'rb') as file_data:
            file_name = os.path.basename(file_path)
            files = {
                'file': (file_name, file_data)
            }
            response = requests.put(f"{GITLAB_PACKAGE_REGISTRY_URL}/{file_name}", headers=headers, files=files, verify=False)

            if response.status_code == 201:
                print(f"File {file_name} uploaded to GitLab Package Registry.")
            else:
                print(f"Failed to upload {file_name} to Package Registry. Status Code: {response.status_code}, Response: {response.content}")

        # Upload the metadata file
        with open(metadata_file_path, 'rb') as metadata_data:
            metadata_file_name = os.path.basename(metadata_file_path)
            files = {
                'file': (metadata_file_name, metadata_data)
            }
            response = requests.put(f"{GITLAB_PACKAGE_REGISTRY_URL}/{metadata_file_name}", headers=headers, files=files, verify=False)

            if response.status_code == 201:
                print(f"Metadata file {metadata_file_name} uploaded to GitLab Package Registry.")
            else:
                print(f"Failed to upload {metadata_file_name} to Package Registry. Status Code: {response.status_code}, Response: {response.content}")

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

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"GitLab pipeline triggered successfully for {file_path}")
        else:
            print(f"Failed to trigger GitLab pipeline. Status Code: {response.status_code}, Response: {response.content}")

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

if __name__ == "__main__":
    watcher = Watcher(FOLDER_TO_WATCH)
    watcher.run()
