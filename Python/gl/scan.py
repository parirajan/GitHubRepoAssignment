import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from urllib.parse import quote

# Configuration
GITLAB_API = "https://gitlab.com/api/v4"
TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"  # Replace with your GitLab Personal Access Token
OUTPUT_DIR = "./downloads"
TARGET_FILENAME = "envoy.json"
BRANCHES_TO_TRY = ["main", "master", "develop"]
MAX_WORKERS = 10

HEADERS = {
    "Private-Token": TOKEN
}


# Get all accessible projects
def get_all_projects():
    projects = []
    page = 1
    while True:
        url = f"{GITLAB_API}/projects"
        params = {"membership": True, "per_page": 100, "page": page}
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error fetching projects: {response.text}")
            break
        page_data = response.json()
        if not page_data:
            break
        projects.extend(page_data)
        page += 1
    return projects


# Search the project tree and download envoy.json
def find_and_download_file(project_id, project_name):
    for branch in BRANCHES_TO_TRY:
        tree_url = f"{GITLAB_API}/projects/{project_id}/repository/tree"
        params = {"ref": branch, "recursive": True, "per_page": 100}
        r = requests.get(tree_url, headers=HEADERS, params=params)

        if r.status_code != 200:
            continue

        tree = r.json()
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith(TARGET_FILENAME):
                file_path = item["path"]
                encoded_path = quote(file_path, safe='')
                file_url = f"{GITLAB_API}/projects/{project_id}/repository/files/{encoded_path}/raw"
                file_resp = requests.get(file_url, headers=HEADERS, params={"ref": branch})

                if file_resp.status_code == 200:
                    local_path = os.path.join(OUTPUT_DIR, project_name)
                    os.makedirs(local_path, exist_ok=True)
                    with open(os.path.join(local_path, os.path.basename(file_path)), 'w') as f:
                        f.write(file_resp.text)
                    return f"Downloaded from branch {branch}: {file_path}"
                else:
                    return f"Failed to download {file_path}: HTTP {file_resp.status_code}"
    return f"{TARGET_FILENAME} not found in branches {BRANCHES_TO_TRY}"


# Threaded download wrapper
def process_project(project):
    project_id = project['id']
    project_name = project['path_with_namespace'].replace("/", "_")
    try:
        result = find_and_download_file(project_id, project_name)
        return project_name, result
    except Exception as e:
        return project_name, f"Error: {str(e)}"


# Main
if __name__ == "__main__":
    print("Connecting to GitLab...")
    all_projects = get_all_projects()
    print(f"Found {len(all_projects)} projects.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_project, p) for p in all_projects]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading envoy.json files"):
            project_name, result = future.result()
            print(f"[{project_name}] -> {result}")
