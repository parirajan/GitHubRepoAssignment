import requests
import json

# Okta API base URL and token
OKTA_BASE_URL = "https://<your_okta_domain>.okta.com"  # Replace with your Okta domain
OKTA_API_TOKEN = "your_okta_token"  # Replace with your Okta API token
HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json"
}

def get_app_id_by_name(app_name):
    """Get the application ID by the application name."""
    apps_url = f"{OKTA_BASE_URL}/api/v1/apps"
    params = {"q": app_name, "limit": 100}  # Use the 'q' parameter to search for the app by name
    
    response = requests.get(apps_url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        response.raise_for_status()

    apps = response.json()
    
    # Check if we found an app with the given name
    if not apps:
        print(f"No application found with the name '{app_name}'.")
        return None

    # Assuming the first match is the desired app
    return apps[0]['id']

def list_users_in_app(app_id):
    """List all users assigned to a specific application (app)."""
    app_users_url = f"{OKTA_BASE_URL}/api/v1/apps/{app_id}/users"
    users = []
    params = {"limit": 100}
    
    while app_users_url:
        response = requests.get(app_users_url, headers=HEADERS, params=params if '?' not in app_users_url else None)

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        users.extend(response.json())
        
        # Check for pagination in the 'Link' header
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            app_users_url = next_link  # Use the next URL, which already contains the 'after' and 'limit' parameters
        else:
            break

    return users

def save_to_json(data, filename):
    """Save the user-app mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    app_name = "YourAppName"  # Replace with your application name
    
    print(f"Fetching app ID for application '{app_name}'...")
    app_id = get_app_id_by_name(app_name)
    
    if app_id:
        print(f"App ID for '{app_name}': {app_id}")
        
        print(f"Fetching users assigned to the application '{app_name}'...")
        users = list_users_in_app(app_id)
        
        # Prepare the list of users for saving
        user_list = [{"id": user['id'], "email": user['profile']['email'], "fullName": f"{user['profile']['firstName']} {user['profile']['lastName']}"} for user in users]
        
        # Save to JSON file
        save_to_json(user_list, filename=f"app_{app_name}_users.json")
        print(f"Users for the application '{app_name}' have been saved to 'app_{app_name}_users.json'.")
    else:
        print(f"Application '{app_name}' not found.")
