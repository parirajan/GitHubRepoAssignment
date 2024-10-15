import requests
import json

# Okta API base URL and token
OKTA_BASE_URL = "https://<your_okta_domain>.okta.com"  # Replace with your Okta domain
OKTA_API_TOKEN = "your_okta_token"  # Replace with your Okta API token
HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json"
}

def get_group_id_by_name(group_name):
    """Retrieve the group ID by group name."""
    groups_url = f"{OKTA_BASE_URL}/api/v1/groups"
    params = {"q": group_name}
    
    response = requests.get(groups_url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        response.raise_for_status()

    groups = response.json()

    if not groups:
        print(f"No group found with the name '{group_name}'.")
        return None

    # Assuming the first match is the group you're looking for
    return groups[0]['id']

def list_users_in_group(group_id):
    """List all users in the specified group."""
    group_users_url = f"{OKTA_BASE_URL}/api/v1/groups/{group_id}/users"
    users = []
    params = {"limit": 100}
    
    while group_users_url:
        response = requests.get(group_users_url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        users.extend(response.json())
        
        # Check for pagination
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            group_users_url = next_link
        else:
            break

    return users

def save_to_json(data, filename='group_users_mapping.json'):
    """Save the user-group mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    group_name = "ApplicationGroupName"  # Replace with your application group name
    print(f"Fetching group ID for group '{group_name}'...")
    
    group_id = get_group_id_by_name(group_name)
    
    if group_id:
        print(f"Group ID for '{group_name}': {group_id}")
        
        print(f"Fetching users in group '{group_name}'...")
        users = list_users_in_group(group_id)
        
        # Display users and save them to a file
        user_list = [{"id": user['id'], "email": user['profile']['email'], "fullName": f"{user['profile']['firstName']} {user['profile']['lastName']}"} for user in users]
        save_to_json(user_list, filename=f"{group_name}_users.json")

        print(f"Users in the group '{group_name}' have been saved to '{group_name}_users.json'.")
    else:
        print(f"Group '{group_name}' not found.")
