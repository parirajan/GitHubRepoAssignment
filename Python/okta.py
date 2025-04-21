import requests

# === CONFIGURE THESE ===
OKTA_DOMAIN = "https://your-okta-domain.okta.com"
API_TOKEN = "your-api-token"
HEADERS = {
    "Authorization": f"SSWS {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def list_groups():
    url = f"{OKTA_DOMAIN}/api/v1/groups"
    groups = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        groups.extend(response.json())
        url = response.links.get('next', {}).get('url')
    return groups

def list_users_in_group(group_id):
    url = f"{OKTA_DOMAIN}/api/v1/groups/{group_id}/users"
    users = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        users.extend(response.json())
        url = response.links.get('next', {}).get('url')
    return users

def main():
    groups = list_groups()
    print(f"Found {len(groups)} groups\n")

    for group in groups:
        group_id = group['id']
        group_name = group['profile']['name']
        print(f"Group: {group_name} (ID: {group_id})")

        users = list_users_in_group(group_id)
        for user in users:
            user_profile = user['profile']
            print(f"  - {user_profile['login']} ({user_profile.get('firstName', '')} {user_profile.get('lastName', '')})")
        print()

if __name__ == "__main__":
    main()
