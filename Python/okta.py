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
    """Fetch users from Okta with pagination."""
    users_url = f"{OKTA_BASE_URL}/api/v1/users"
    users = []
    params = {"limit": 100}  # Set the limit to fetch users in batches of 100
    after_token = None  # Initialize after_token as None

    while True:
        # If we have an after token, add it to the params
        if after_token:
            params['after'] = after_token

        print(f"Fetching data from: {users_url} with params {params}")
        response = requests.get(users_url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        users.extend(response.json())

        # Check for 'next' link in the pagination headers
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            after_token = next_link.split('after=')[1].split('&')[0]  # Extract the new after token
        else:
            break  # No more pages

    return users

def save_to_json(data, filename='user_group_mapping.json'):
    """Save the mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    users = get_okta_users()
    save_to_json(users)
    print("User data has been saved to user_group_mapping.json")
