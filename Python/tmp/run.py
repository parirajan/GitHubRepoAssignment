import requests
import time
import uuid
import random
import string
from datetime import datetime, timedelta

# Base URL for the request
url = "http://your-url-here"   # <== Replace with your actual target URL

# Fixed payload fields from payload.json
payload_keys = [
    "CdtrAcct_Id_IBAN",
    "CdtrAcct_Id_Othr_Id",
    "CdtrAcct_Prxy_Id",
    "CdtrAcct_Tp_Cd",
    "CdtrAcct_Tp_Prtry",
    "CdtrAgt_FinInstnId_ClrSysMmbId_MmbId",
    "CtgyPurp_Cd",
    "CtgyPurp_Prtry",
    "DbtrAcct_Id_IBAN",
    "DbtrAcct_Id_Othr_Id",
    "DbtrAcct_Prxy_Id",
    "DbtrAcct_Tp_Cd",
    "DbtrAcct_Tp_Prtry",
    "DbtrAgt_FinInstnId_ClrSysMmbId_MmbId",
    "Derive_Screen_Unique_ID",
    "InstgAgt_FinInstnId_ClrSysMmbId_MmbId",
    "IntrBkSttlmAmt",
    "Non_ISO_API_Version",
    "Non_ISO_Sender_Connection_Party",
    "Non_ISO_Transaction_Receive_Dtm",
    "Non_ISO_reference_id",
    "Non_ISO_transaction_type_cd",
    "Purp_Cd",
    "Purp_Prtry",
    "SP_MessageTypeID"
]

def random_string(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def random_code(length=4):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def random_iban(country='DE'):
    bank_code = ''.join(random.choices(string.digits, k=8))
    account_number = ''.join(random.choices(string.digits, k=10))
    return f"{country}89{bank_code}{account_number}"

def random_float(min_val=1000.00, max_val=100000.00, decimals=2):
    return round(random.uniform(min_val, max_val), decimals)

def random_datetime():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

def generate_payload():
    payload = {}
    for key in payload_keys:
        key_lower = key.lower()

        if "iban" in key_lower:
            payload[key] = random_iban()
        elif "amount" in key_lower or "amt" in key_lower:
            payload[key] = random_float()
        elif "dtm" in key_lower or "dt" in key_lower or "date" in key_lower:
            payload[key] = random_datetime()
        elif "id" in key_lower and "iban" not in key_lower:
            payload[key] = str(uuid.uuid4())
        elif "code" in key_lower or "cd" in key_lower:
            payload[key] = random_code()
        elif "version" in key_lower or "message" in key_lower:
            payload[key] = random.randint(1000, 99999)
        elif "prtry" in key_lower or "party" in key_lower or "name" in key_lower:
            payload[key] = random_string(12)
        else:
            payload[key] = random_string(10)
    return payload

headers = {
    'Content-Type': 'application/json',
    'X-SP-Request-Type': 'ModelRequest',
    'X-SP-Message-Type-Id': '2'
}

def send_request():
    payload = generate_payload()
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

def main():
    while True:
        start_time = time.time()
        for _ in range(30):  # Send 30 requests per second
            status_code, response_text = send_request()
            print(f"Status Code: {status_code}, Response: {response_text}")
            elapsed_time = time.time() - start_time
            sleep_time = max(0, 1 - elapsed_time)
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()
