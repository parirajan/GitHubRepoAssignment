import requests
import csv
import base64

# === CONFIGURATION ===
OKTA_DOMAIN = "https://your-okta-domain.okta.com"
AUTH_SERVER_ID = "default"  # Or your custom authorization server ID
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
NAMESPACE_LABEL = "Salesforce"  # The App Label (namespace) you're querying under

def get_oauth2_token():
    token_url = f"{OKTA_DOMAIN}/oauth2/{AUTH_SERVER_ID}/v1/token"
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    headers = {
        "Authorization": "Basic " + base64.b64encode(credentials.encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "okta.groups.read okta.users.read okta.apps.read"
    }
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def find_app_by_label(app_label, headers):
    url = f"{OKTA_DOMAIN}/api/v1/apps?q={app_label}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    apps = response.json()
    for app in apps:
        if app.get("label", "").lower() == app_label.lower():
            return app
    return None

def list_groups_assigned_to_app(app_id, headers):
    url = f"{OKTA_DOMAIN}/api/v1/apps/{app_id}/groups"
    groups = []
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        groups.extend(response.json())
        url = response.links.get("next", {}).get("url")
    return groups

def list_users_in_group(group_id, headers):
    url = f"{OKTA_DOMAIN}/api/v1/groups/{group_id}/users"
    users = []
    while url:
        response = requests.get(url, headers=headers)
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
    access_token = get_oauth2_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    app = find_app_by_label(NAMESPACE_LABEL, headers)
    if not app:
        print(f"App with label '{NAMESPACE_LABEL}' not found.")
        return

    app_id = app["id"]
    print(f"Found app '{NAMESPACE_LABEL}' with ID: {app_id}")

    groups = list_groups_assigned_to_app(app_id, headers)
    print(f"Found {len(groups)} groups assigned to '{NAMESPACE_LABEL}'")

    result_rows = []

    for group in groups:
        group_name = group["profile"]["name"]
        group_id = group["id"]
        users = list_users_in_group(group_id, headers)

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
    print("Export complete: namespace_group_users.csv")

if __name__ == "__main__":
    main()
