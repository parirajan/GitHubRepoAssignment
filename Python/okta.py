import requests
import json

# Okta API base URL and token
OKTA_BASE_URL = "https://<your_okta_domain>.okta.com"  # Replace with your Okta domain
OKTA_API_TOKEN = "your_okta_token"  # Replace with your Okta API token
HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json"
}

def get_all_apps():
    """Fetch all applications (apps) from Okta."""
    apps_url = f"{OKTA_BASE_URL}/api/v1/apps"
    apps = []
    params = {"limit": 100}
    
    while apps_url:
        response = requests.get(apps_url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        apps.extend(response.json())
        
        # Check for pagination
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            apps_url = next_link
        else:
            break

    return apps

def list_users_in_app(app_id):
    """List all users assigned to a specific application (app)."""
    app_users_url = f"{OKTA_BASE_URL}/api/v1/apps/{app_id}/users"
    users = []
    params = {"limit": 100}
    
    while app_users_url:
        response = requests.get(app_users_url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        users.extend(response.json())
        
        # Check for pagination
        next_link = response.links.get('next', {}).get('url')
        if next_link:
            app_users_url = next_link
        else:
            break

    return users

def map_users_to_apps():
    """Map users to their assigned applications and group by application name."""
    apps = get_all_apps()
    app_user_mapping = {}

    for app in apps:
        app_id = app['id']
        app_name = app['label']
        print(f"Fetching users for application: {app_name} (ID: {app_id})")
        
        users = list_users_in_app(app_id)
        user_list = [{"id": user['id'], "email": user['profile']['email'], "fullName": f"{user['profile']['firstName']} {user['profile']['lastName']}"} for user in users]
        
        app_user_mapping[app_name] = user_list  # Group users by application name

    return app_user_mapping

def save_to_json(data, filename='app_user_mapping.json'):
    """Save the app-user mapping to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    print("Fetching applications and their assigned users...")
    app_user_mapping = map_users_to_apps()

    print("Saving application-user mapping to JSON file...")
    save_to_json(app_user_mapping, filename="app_user_mapping.json")
    
    print("Application-user mapping has been saved to 'app_user_mapping.json'.")
