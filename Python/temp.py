import time
import hashlib
import os
import datetime
import requests
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
        if event.event_type in ("modified", "created") and not event.is_directory:
            file_path = event.src_path

            # 1. Calculate the checksum and timestamp
            file_checksum = self.calculate_checksum(file_path)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Create a metadata file with the checksum and timestamp
            metadata_file_path = self.create_metadata_file(file_path, file_checksum, timestamp)

            # 3. Upload the file and metadata to GitLab Package Registry
            self.upload_to_package_registry(file_path)
            self.upload_to_package_registry(metadata_file_path)

            # 4. Trigger the GitLab CI pipeline to validate the uploaded file in the package registry
            self.trigger_gitlab_pipeline(file_path)

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
        Create a file containing the checksum and timestamp.
        """
        metadata_file_path = f"{file_path}.metadata.txt"
        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write(f"File: {os.path.basename(file_path)}\n")
            metadata_file.write(f"Checksum (SHA-256): {checksum}\n")
            metadata_file.write(f"Timestamp: {timestamp}\n")

        print(f"Metadata file created: {metadata_file_path}")
        return metadata_file_path

    def upload_to_package_registry(self, file_path):
        """
        Upload the file to GitLab Package Registry using the GitLab API.
        """
        with open(file_path, 'rb') as file_data:
            file_name = os.path.basename(file_path)
            headers = {
                "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN
            }
            files = {
                'file': (file_name, file_data)
            }

            response = requests.put(f"{GITLAB_PACKAGE_REGISTRY_URL}/{file_name}", headers=headers, files=files)

            if response.status_code == 201:
                print(f"File {file_name} uploaded to GitLab Package Registry.")
            else:
                print(f"Failed to upload {file_name} to Package Registry. Status Code: {response.status_code}, Response: {response.content}")

    def trigger_gitlab_pipeline(self, file_path):
        """
        Trigger a GitLab CI/CD pipeline to validate the uploaded artifact in the package registry using the GitLab API.
        """
        url = f"{GITLAB_API_URL}/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "token": GITLAB_TRIGGER_TOKEN,
            "ref": GITLAB_REF,
            "variables": {
                "UPDATED_FILE": os.path.basename(file_path)  # Pass the updated file as a variable
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
