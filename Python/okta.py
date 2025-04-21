import requests
import csv

# === CONFIGURE THESE ===
OKTA_DOMAIN = "https://your-okta-domain.okta.com"
API_TOKEN = "your-okta-api-token"
NAMESPACE_LABEL = "Salesforce"  # 👈 App Label you're treating as a namespace

HEADERS = {
    "Authorization": f"SSWS {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def find_app_by_label(label):
    url = f"{OKTA_DOMAIN}/api/v1/apps?q={label}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    apps = response.json()
    for app in apps:
        if app.get("label", "").lower() == label.lower():
            return app
    return None

def list_groups_assigned_to_app(app_id):
    url = f"{OKTA_DOMAIN}/api/v1/apps/{app_id}/groups"
    groups = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        groups.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return groups

def list_users_in_group(group_id):
    url = f"{OKTA_DOMAIN}/api/v1/groups/{group_id}/users"
    users = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        users.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return users

def export_to_csv(data, filename):
    with open(filename, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "app_label", "group_name", "user_login", "first_name", "last_name"
        ])
        writer.writeheader()
        writer.writerows(data)

def main():
    app = find_app_by_label(NAMESPACE_LABEL)
    if not app:
        print(f"❌ App with label '{NAMESPACE_LABEL}' not found.")
        return

    app_id = app["id"]
    print(f"✅ Found app '{NAMESPACE_LABEL}' with ID: {app_id}")

    groups = list_groups_assigned_to_app(app_id)
    print(f"🔍 Found {len(groups)} groups assigned to '{NAMESPACE_LABEL}'")

    result_rows = []

    for group in groups:
        group_name = group["profile"]["name"]
        group_id = group["id"]
        users = list_users_in_group(group_id)

        for user in users:
            profile = user["profile"]
            result_rows.append({
                "app_label": NAMESPACE_LABEL,
                "group_name": group_name,
                "user_login": profile.get("login"),
                "first_name": profile.get("firstName", ""),
                "last_name": profile.get("lastName", "")
            })

    export_to_csv(result_rows, "namespace_group_users.csv")
    print("✅ Export complete: namespace_group_users.csv")

if __name__ == "__main__":
    main()
