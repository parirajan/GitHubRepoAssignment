import requests
import time
import random
from datetime import datetime, timedelta

# List of URLs for the 6 nodes
urls = [
    "http://localhost:27911",
    "http://localhost:27912",
    "http://localhost:27913",
    "http://localhost:27914",
    "http://localhost:27915",
    "http://localhost:27916"
]

# Function to generate a new transaction request payload
def generate_payload():
    message_id = random.randint(1, 100000)  # Generate a random MsgId between 1 and 100,000
    transaction_receive_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]  # Current time in UTC
    transaction_final_time = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]  # Final time 10 seconds after receive time
    amount = round(100 * (1 + 0.01 * (2 * (0.5 - random.random()))), 2)  # Random amount close to 100

    payload = {
        "MsgId": message_id,
        "TransactionReceiveDtm": transaction_receive_time,
        "TransactionFinalDtm": transaction_final_time,
        "TransactionTypeCd": "PACS008",
        "StatusCd": "Settled",
        "Amount": amount,
        "FraudScreenDataArray": [1, 0, 1, 0],
        "ProprietaryRejectionCdArray": []
    }
    
    return payload

# Headers for the request
headers = {
    'Content-Type': 'text/json',
    'X-SP-Request-Type': 'ModelRequest',
    'X-SP-Message-Type-Id': '1'
}

# Function to send a single request to a specific URL
def send_request(url):
    payload = generate_payload()
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

# Main function to send 100 requests per second distributed across 6 nodes
def main():
    url_index = 0
    while True:
        start_time = time.time()
        for _ in range(100):
            # Round-robin selection of the URL
            current_url = urls[url_index]
            status_code, response_text = send_request(current_url)
            print(f"URL: {current_url}, Status Code: {status_code}, Response: {response_text}")
            # Move to the next URL in the list
            url_index = (url_index + 1) % len(urls)
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1 - elapsed_time)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
