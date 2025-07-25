import os
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Configuration ---
GITLAB_API = "https://gitlab.com/api/v4"
TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"  # Replace with your PAT
HEADERS = {"Private-Token": TOKEN}
OUTPUT_DIR = "./downloads"
TARGET_FILENAME = "envoy.json"
SUBDIR = "application"
BRANCHES_TO_TRY = ["main", "master", "develop"]
MAX_WORKERS = 10

# --- Group & Project Discovery ---
def get_all_groups():
    groups = []
    page = 1
    while True:
        r = requests.get(
            f"{GITLAB_API}/groups",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "min_access_level": 10}
        )
        if r.status_code != 200:
            print(f"Error fetching groups: {r.text}")
            break
        page_groups = r.json()
        groups.extend(page_groups)
        next_page = r.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)
    return groups

def get_all_subgroups(group_id):
    subgroups = []
    page = 1
    while True:
        r = requests.get(
            f"{GITLAB_API}/groups/{group_id}/subgroups",
            headers=HEADERS,
            params={"per_page": 100, "page": page}
        )
        if r.status_code != 200:
            break
        page_subgroups = r.json()
        subgroups.extend(page_subgroups)
        next_page = r.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)
    for sg in subgroups[:]:
        subgroups.extend(get_all_subgroups(sg["id"]))
    return subgroups

def get_projects_from_group(group_id):
    projects = []
    page = 1
    while True:
        r = requests.get(
            f"{GITLAB_API}/groups/{group_id}/projects",
            headers=HEADERS,
            params={"per_page": 100, "page": page}
        )
        if r.status_code != 200:
            break
        page_projects = r.json()
        projects.extend(page_projects)
        next_page = r.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)
    return projects

def get_all_projects_from_all_groups():
    all_projects = []
    top_groups = get_all_groups()
    for group in top_groups:
        print(f"Scanning group: {group['full_path']}")
        all_projects.extend(get_projects_from_group(group['id']))
        subgroups = get_all_subgroups(group['id'])
        for sg in subgroups:
            print(f"  Scanning subgroup: {sg['full_path']}")
            all_projects.extend(get_projects_from_group(sg['id']))
    return all_projects

# --- File Search & Download ---
def find_and_download_from_application_dir(project_id, project_name):
    for branch in BRANCHES_TO_TRY:
        tree_url = f"{GITLAB_API}/projects/{project_id}/repository/tree"
        params = {
            "ref": branch,
            "path": SUBDIR,
            "recursive": True,
            "per_page": 100
        }
        r = requests.get(tree_url, headers=HEADERS, params=params)
        if r.status_code != 200:
            continue
        tree = r.json()
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith(f"{SUBDIR}/{TARGET_FILENAME}"):
                file_path = item["path"]
                encoded_path = quote(file_path, safe='')
                file_url = f"{GITLAB_API}/projects/{project_id}/repository/files/{encoded_path}/raw"
                file_resp = requests.get(file_url, headers=HEADERS, params={"ref": branch})
                if file_resp.status_code == 200:
                    local_path = os.path.join(OUTPUT_DIR, project_name)
                    os.makedirs(local_path, exist_ok=True)
                    with open(os.path.join(local_path, TARGET_FILENAME), 'w') as f:
                        f.write(file_resp.text)
                    return f"Downloaded {file_path} from branch {branch}"
                else:
                    return f"Failed to download: HTTP {file_resp.status_code}"
    return f"{SUBDIR}/{TARGET_FILENAME} not found in any branch"

# --- Parallel Processing ---
def process_project(project):
    project_id = project['id']
    project_name = project['path_with_namespace'].replace("/", "_")
    try:
        result = find_and_download_from_application_dir(project_id, project_name)
        return project_name, result
    except Exception as e:
        return project_name, f"Error: {str(e)}"

# --- Main ---
if __name__ == "__main__":
    print("Discovering projects from all groups and subgroups...")
    all_projects = get_all_projects_from_all_groups()
    print(f"Total projects discovered: {len(all_projects)}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_project, p) for p in all_projects]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading envoy.json"):
            project_name, result = future.result()
            print(f"[{project_name}] -> {result}")
