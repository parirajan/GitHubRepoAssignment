import os
import sys
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import shutil

# Redirect stdout and stderr to a log file to prevent CI log overflow
sys.stdout = open("scan_output.log", "w")
sys.stderr = sys.stdout

print("Starting scan for specified project list...", file=sys.__stdout__)

# Configuration
GITLAB_API = os.environ.get("CI_API_V4_URL", "https://gitlab.com/api/v4")
TOKEN = os.environ.get("GITLAB_API_TOKEN")  # Set this in GitLab CI/CD variables
HEADERS = {"Private-Token": TOKEN}
OUTPUT_DIR = "./downloads"
TARGET_FILENAME = "envoy.json"
SUBDIR = "application"
BRANCHES_TO_TRY = ["main", "master", "develop"]
MAX_WORKERS = 4  # Safe default for CI runners

# Read project paths from input file (one per line)
def read_project_list(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Get project info from full path like "group/subgroup/project"
def get_project_by_path(path):
    encoded_path = quote(path, safe='')
    r = requests.get(f"{GITLAB_API}/projects/{encoded_path}", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"[WARN] Could not access project: {path} ({r.status_code})", file=sys.__stdout__)
        return None

# Search for envoy.json inside the 'application' folder and download it
def find_and_download_envoy_json(project_id, project_name):
    for branch in BRANCHES_TO_TRY:
        params = {"ref": branch, "path": SUBDIR, "recursive": True, "per_page": 100}
        r = requests.get(f"{GITLAB_API}/projects/{project_id}/repository/tree", headers=HEADERS, params=params, timeout=10)
        if r.status_code != 200:
            continue

        tree = r.json()
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith(f"{SUBDIR}/{TARGET_FILENAME}"):
                file_path = item["path"]
                encoded_file_path = quote(file_path, safe='')
                file_url = f"{GITLAB_API}/projects/{project_id}/repository/files/{encoded_file_path}/raw"
                resp = requests.get(file_url, headers=HEADERS, params={"ref": branch}, timeout=10)

                if resp.status_code == 200:
                    local_path = os.path.join(OUTPUT_DIR, project_name)
                    os.makedirs(local_path, exist_ok=True)
                    with open(os.path.join(local_path, TARGET_FILENAME), 'w') as f:
                        f.write(resp.text)
                    return f"Downloaded from {branch}: {file_path}"
                else:
                    return f"Failed to download from {branch}: HTTP {resp.status_code}"
    return f"{TARGET_FILENAME} not found in {SUBDIR} for any branch"

# Process one project
def process_project_path(project_path):
    project = get_project_by_path(project_path)
    if not project:
        return project_path.replace('/', '_'), "Not accessible or not found"
    project_id = project['id']
    project_name = project['path_with_namespace'].replace('/', '_')
    result = find_and_download_envoy_json(project_id, project_name)
    return project_name, result

# Main entry point
if __name__ == "__main__":
    project_list_file = "project_list.txt"  # Must be committed or mounted into CI job
    if not os.path.exists(project_list_file):
        print("project_list.txt not found", file=sys.__stdout__)
        sys.exit(1)

    project_paths = read_project_list(project_list_file)
    print(f"Total projects to scan: {len(project_paths)}", file=sys.__stdout__)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_project_path, p) for p in project_paths]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Scanning projects"):
            project_name, result = future.result()
            print(f"[{project_name}] -> {result}")

    print("Zipping output...", file=sys.__stdout__)
    if os.path.exists("downloads") and os.listdir("downloads"):
        shutil.make_archive("envoy_json_output", "zip", "downloads")
        print("Zipped output to envoy_json_output.zip", file=sys.__stdout__)
    else:
        print("No files downloaded. Skipping ZIP creation.", file=sys.__stdout__)

    print("All downloads completed.", file=sys.__stdout__)
    sys.stdout.close()
