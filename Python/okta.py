import requests
import json
import urllib.parse

# Okta API base URL and token
OKTA_BASE_URL = "https://<your_okta_domain>.okta.com"  # Replace with your Okta domain
OKTA_API_TOKEN = "your_read_only_token"  # Replace with your Okta API token
HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json"
}

def get_okta_users():
    """Fetch users from Okta with pagination."""
    users_url = f"{OKTA_BASE_URL}/api/v1/users"
    users = []
    params = {"limit": 100}  # Set the limit to fetch users in batches of 100
    after_token = None  # Initialize after_token as None

    while True:
        if after_token:
            params['after'] = after_token  # Use the after token for pagination

        print(f"Fetching data from: {users_url} with params {params}")
        response = requests.get(users_url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        users.extend(response.json())  # Add the fetched users to the list

        # Check for 'next' link in the pagination headers
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            after_token = next_link.split('after=')[1].split('&')[0]  # Extract the new after token
        else:
            break  # No more pages

    return users

def get_user_groups(user_id):
    """Fetch the groups for a specific user."""
    groups_url = f"{OKTA_BASE_URL}/api/v1/users/{user_id}/groups"
    response = requests.get(groups_url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error fetching groups for user {user_id}: {response.status_code} - {response.text}")
        response.raise_for_status()

    return response.json()  # Return the list of groups the user belongs to

def map_users_to_groups(users):
    """Map each user to their respective groups."""
    user_group_mapping = {}

    for user in users:
        user_id = user['id']
        user_name = user['profile']['login']
        print(f"Fetching groups for user: {user_name} (ID: {user_id})")
        
        groups = get_user_groups(user_id)  # Fetch the groups for this user
        group_names = [group['profile']['name'] for group in groups]  # Extract group names
        user_group_mapping[user_name] = group_names  # Map the user to their groups

    return user_group_mapping

def save_to_json(data, filename='user_group_mapping.json'):
    """Save the user-group mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    print("Fetching users from Okta...")
    users = get_okta_users()  # Fetch all users

    print("Mapping users to their groups...")
    user_group_mapping = map_users_to_groups(users)  # Map users to their groups

    print("Saving user-group mapping to JSON file...")
    save_to_json(user_group_mapping)  # Save the mapping to a JSON file

    print("User-group mapping has been saved to 'user_group_mapping.json'.")
