import requests
import os

# --- Config ---
GITLAB_API = "https://gitlab.com/api/v4"
TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"
OUTPUT_DIR = "./downloads"
FILE_PATH = "envoy.json"
BRANCHES_TO_TRY = ["main", "master"]

HEADERS = {
    "Private-Token": TOKEN
}

# --- Helpers ---
def get_all_projects():
    projects = []
    page = 1
    while True:
        response = requests.get(f"{GITLAB_API}/projects", headers=HEADERS, params={"membership": True, "per_page": 100, "page": page})
        if response.status_code != 200:
            print("Failed to fetch projects:", response.text)
            break
        data = response.json()
        if not data:
            break
        projects.extend(data)
        page += 1
    return projects

def download_file(project_id, project_name):
    for branch in BRANCHES_TO_TRY:
        url = f"{GITLAB_API}/projects/{project_id}/repository/files/{FILE_PATH.replace('/', '%2F')}/raw"
        params = {"ref": branch}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            local_path = os.path.join(OUTPUT_DIR, project_name)
            os.makedirs(local_path, exist_ok=True)
            with open(os.path.join(local_path, FILE_PATH), 'w') as f:
                f.write(r.text)
            print(f"Downloaded {FILE_PATH} from {project_name} [{branch}]")
            return True
    print(f"{FILE_PATH} not found in {project_name}")
    return False

# --- Main ---
if __name__ == "__main__":
    all_projects = get_all_projects()
    print(f"Found {len(all_projects)} projects.")

    for project in all_projects:
        download_file(project['id'], project['path_with_namespace'].replace("/", "_"))
