import requests
import time
import uuid
import random
import string
from datetime import datetime, timedelta

# List of node URLs (replace these with real URLs)
nodes = [
    "http://node1-url-here",
    "http://node2-url-here",
    "http://node3-url-here"
]
node_index = 0

# Payload keys 
payload_keys = [
    "IntrBkSttlmAmt",
    "SP_MessageTypeID",
    "SP_FraudFlag",
    "MsgId",
    "CredDttm",
    "DbtrAcct_Id_IBAN",
    "DbtrAcct_Id_Othr_Id",
    "OrgnlMsgId",
    "Non_ISO_Transaction_Receive_Dtm",
    "UltmtDbtr_Nm",
    "Dbtr_Pty_PstlAdr_Room",
    "Cdtr_Pty_PstlAdr_StrtNm",
    "Non_ISO_API_Version",
    "Non_ISO_Transaction_type_cd",
    "Non_ISO_fraud_screen_data_array",
    "Non_ISO_proprietary_rejection_cd_array",
    "Non_ISO_receiver_response_cd"
]

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
        if "Amt" in key or "Amount" in key:
            payload[key] = random_float()
        elif "Dtm" in key or "Dt" in key or "Date" in key:
            payload[key] = random_datetime()
        elif "Id" in key or "ID" in key or "MsgId" in key:
            payload[key] = str(uuid.uuid4())
        elif "Nm" in key or "Name" in key:
            payload[key] = random_string(10)
        elif "Cd" in key or "Code" in key:
            payload[key] = random_string(5)
        elif "Room" in key or "Adr" in key or "Addr" in key or "Line" in key:
            payload[key] = random_string(12)
        elif "array" in key.lower():
            payload[key] = random_array()
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

    # Select next node (round robin)
    url = nodes[node_index]
    node_index = (node_index + 1) % len(nodes)

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
