import json
import random
import requests
from datetime import datetime
import uuid

# Constants
ENDPOINT = "http://localhost:8080/"
INPUT_FILE = "mtid1_transactions.jsonl"
MTID = 4
NUM_REQUESTS = 50

HEADERS = {
    "Content-Type": "application/json",
    "SP_MessageTypeID": str(MTID)
}

def current_time_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def generate_prescreen_request(base_txn):
    return {
        "CdtrAcct_Id_IBAN": base_txn["CdtrAcct_Id_IBAN"],
        "CdtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "CdtrAcct_Prxy_Id": str(uuid.uuid4()),
        "CdtrAcct_Tp_Cd": "CACC",
        "CdtrAcct_Tp_Prtry": "SAVINGS",
        "CdtrAgt_FinInstnId_ClrSysMmbId_MmbId": base_txn["CdtrAgt_FinInstnId_ClrSysMmbId_MmbId"],

        "DbtrAcct_Id_IBAN": base_txn["DbtrAcct_Id_IBAN"],
        "DbtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "DbtrAcct_Prxy_Id": str(uuid.uuid4()),
        "DbtrAcct_Tp_Cd": "CACC",
        "DbtrAcct_Tp_Prtry": "CHECKING",
        "DbtrAgt_FinInstnId_ClrSysMmbId_MmbId": base_txn["DbtrAgt_FinInstnId_ClrSysMmbId_MmbId"],

        "InstgAgt_FinInstnId_ClrSysMmbId_MmbId": base_txn["DbtrAgt_FinInstnId_ClrSysMmbId_MmbId"],
        "Derive_Screen_Unique_ID": "insight-" + str(uuid.uuid4()),
        "IntrBkSttlmAmt": round(random.uniform(20.0, 10000.0), 2),
        "IntrBkSttlmAmt_@Ccy": "USD",

        "CtgyPurp_Cd": "CP01",
        "CtgyPurp_Prtry": "MERCH",
        "Purp_Cd": "GDDS",
        "Prty_Prtry": "NORM",

        "Non_ISO_transaction_type_cd": "pacs.008",
        "Non_ISO_Sender_Connection_Party": "PrescreenService",
        "Non_ISO_transaction_Receive_Dtm": current_time_str(),
        "Non_ISO_API_Version": 1,
        "SP_MessageTypeID": MTID
    }

def main():
    with open(INPUT_FILE, "r") as f:
        transactions = [json.loads(line) for line in f if line.strip()]

    selected = random.sample(transactions, min(NUM_REQUESTS, len(transactions)))

    for txn in selected:
        payload = generate_prescreen_request(txn)
        response = requests.post(ENDPOINT, headers=HEADERS, json=payload)

        print("\nSubmitted Prescreen Request:")
        print(json.dumps(payload, indent=2))
        print("Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)

if __name__ == "__main__":
    main()
