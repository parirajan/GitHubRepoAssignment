import requests
import time
import uuid
from datetime import datetime, timedelta

# Base URL for the request
url = "http://localhost:27911"

# Function to generate a new transaction request payload
def generate_payload():
    message_id = str(uuid.uuid4())  # Generate a unique message ID
    transaction_receive_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]  # Current time in UTC
    transaction_final_time = (datetime.utcnow() + timedelta(seconds=10)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]  # Final time 10 seconds after receive time
    amount = round(100 * (1 + 0.01 * (2 * (0.5 - uuid.uuid4().int % 1000 / 1000))), 2)  # Random amount close to 100

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

# Function to send a single request
def send_request():
    payload = generate_payload()
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

# Main function to send 100 requests per second
def main():
    while True:
        start_time = time.time()
        for _ in range(100):
            status_code, response_text = send_request()
            print(f"Status Code: {status_code}, Response: {response_text}")
        elapsed_time = time.time() - start_time
        sleep_time = max(0, 1 - elapsed_time)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
