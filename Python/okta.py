import requests
import csv

# === CONFIGURE THESE ===
OKTA_DOMAIN = "https://your-okta-domain.okta.com"
API_TOKEN = "your-okta-api-token"
NAMESPACE_LABEL = "Salesforce"  # 👈 This is your app label namespace

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

def list_users_assigned_to_app(app_id):
    url = f"{OKTA_DOMAIN}/api/v1/apps/{app_id}/users"
    users = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        users.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return users

def list_user_groups(user_id):
    url = f"{OKTA_DOMAIN}/api/v1/users/{user_id}/groups"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def export_to_csv(data, filename):
    with open(filename, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["app_label", "user_login", "first_name", "last_name", "group_name"])
        writer.writeheader()
        writer.writerows(data)

def main():
    app = find_app_by_label(NAMESPACE_LABEL)
    if not app:
        print(f"❌ App with label '{NAMESPACE_LABEL}' not found.")
        return

    app_id = app["id"]
    print(f"✅ Found app '{NAMESPACE_LABEL}' with ID: {app_id}")

    users = list_users_assigned_to_app(app_id)
    print(f"🔍 Found {len(users)} users assigned to '{NAMESPACE_LABEL}'")

    result_rows = []

    for user_entry in users:
        user = user_entry.get("user", {})
        profile = user.get("profile", {})
        user_id = user.get("id")
        login = profile.get("login")
        first = profile.get("firstName", "")
        last = profile.get("lastName", "")

        groups = list_user_groups(user_id)
        if not groups:
            result_rows.append({
                "app_label": NAMESPACE_LABEL,
                "user_login": login,
                "first_name": first,
                "last_name": last,
                "group_name": ""
            })
        for group in groups:
            result_rows.append({
                "app_label": NAMESPACE_LABEL,
                "user_login": login,
                "first_name": first,
                "last_name": last,
                "group_name": group["profile"].get("name", "")
            })

    export_to_csv(result_rows, "namespace_app_users_groups.csv")
    print("✅ Export complete: namespace_app_users_groups.csv")

if __name__ == "__main__":
    main()
