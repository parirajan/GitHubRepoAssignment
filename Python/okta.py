import requests
import json

# Okta API base URL and token
OKTA_BASE_URL = "https://<your_okta_domain>.okta.com"  # Replace with your Okta domain
OKTA_API_TOKEN = "your_read_only_token"  # Replace with your Okta API token
HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json"
}

def get_okta_users():
    """Fetch users from Okta."""
    users_url = f"{OKTA_BASE_URL}/api/v1/users"
    users = []
    params = {"limit": 200}  # Adjust limit as needed
    while users_url:
        response = requests.get(users_url, headers=HEADERS, params=params)
        response.raise_for_status()
        users.extend(response.json())
        users_url = response.links.get('next', {}).get('url')
    return users

def get_user_groups(user_id):
    """Fetch groups for a specific user."""
    groups_url = f"{OKTA_BASE_URL}/api/v1/users/{user_id}/groups"
    response = requests.get(groups_url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def map_users_to_groups():
    """Map users to their respective groups."""
    users = get_okta_users()
    user_group_mapping = {}

    for user in users:
        user_id = user['id']
        user_name = user['profile']['login']
        groups = get_user_groups(user_id)
        group_names = [group['profile']['name'] for group in groups]
        user_group_mapping[user_name] = group_names

    return user_group_mapping

def save_to_json(data, filename='user_group_mapping.json'):
    """Save the mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    user_group_mapping = map_users_to_groups()
    save_to_json(user_group_mapping)
    print("User to group mapping has been saved to user_group_mapping.json")
