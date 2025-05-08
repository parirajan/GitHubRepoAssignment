import requests
import time
import uuid
import random
import string
from datetime import datetime, timedelta

# === Multiple Nodes ===
nodes = [
    "http://node1-url-here",
    "http://node2-url-here",
    "http://node3-url-here"
]
node_index = 0  # Start from first node

# Load payload keys from file (inputs.txt) and remove duplicates
def load_keys(filename):
    with open(filename, "r") as f:
        keys = f.readlines()
    keys = [k.strip() for k in keys if k.strip()]
    return list(set(keys))

payload_keys = load_keys("inputs.txt")

def random_string(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def random_float(min_value=1.0, max_value=10000.0, decimals=2):
    return round(random.uniform(min_value, max_value), decimals)

def random_datetime():
    return (datetime.utcnow() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

def random_boolean():
    return random.choice([True, False])

def random_array():
    return random.choices([0, 1], k=3)

def generate_payload():
    payload = {}
    for key in payload_keys:
        key_lower = key.lower()

        if "amt" in key_lower or "amount" in key_lower:
            payload[key] = random_float()
        elif "dtm" in key_lower or "dt" in key_lower or "date" in key_lower:
            payload[key] = random_datetime()
        elif "id" in key_lower or "msgid" in key_lower:
            payload[key] = str(uuid.uuid4())
        elif "nm" in key_lower or "name" in key_lower:
            payload[key] = random_string(10)
        elif "cd" in key_lower or "code" in key_lower:
            payload[key] = random_string(5)
        elif "room" in key_lower or "adr" in key_lower or "addr" in key_lower or "line" in key_lower:
            payload[key] = random_string(12)
        elif "array" in key_lower:
            payload[key] = random_array()
        elif "flag" in key_lower:
            payload[key] = random_boolean()
        else:
            payload[key] = random_string(8)

    return payload

headers = {
    'Content-Type': 'application/json',
    'X-SP-Request-Type': 'ModelRequest',
    'X-SP-Message-Type-Id': '2'
}

def send_request():
    global node_index

    payload = generate_payload()

    # Pick next node (round robin)
    url = nodes[node_index]
    node_index = (node_index + 1) % len(nodes)  # Move to next, wrap around if needed

    response = requests.post(url, json=payload, headers=headers)
    return url, response.status_code, response.text

def main():
    while True:
        start_time = time.time()
        for _ in range(30):
            url, status_code, response_text = send_request()
            print(f"Node: {url}, Status Code: {status_code}, Response: {response_text}")
            elapsed_time = time.time() - start_time
            sleep_time = max(0, 1 - elapsed_time)
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()
