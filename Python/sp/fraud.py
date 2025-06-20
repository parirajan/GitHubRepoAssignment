import json
import random
import requests
from datetime import datetime

# Constants
ENDPOINT = "http://localhost:8080/"
MTID = 3
INPUT_FILE = "mtid1_transactions.jsonl"
CHUNK_SIZE = 1000
FRAUDS_PER_CHUNK = 3

HEADERS = {
    "Content-Type": "application/json",
    "SP_MessageTypeID": str(MTID)
}

def random_time_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def generate_fraud_report(base_txn):
    return {
        "Derive_Screen_Unique_ID": "fraud-" + str(random.randint(100000, 999999)),
        "FI_Fraud_Action": random.choice(["A", "B", "C"]),
        "FI_Fraud_Submitter_Indicator": random.choice(["A", "B"]),
        "FI_Fraud_Submitting_FI_Contact_Email": "fraud@bank.com",
        "FI_Fraud_Submitting_FI_Contact_Name": "Fraud Analyst",
        "FI_Fraud_Suspicious_Party": "Debtor" if random.random() > 0.5 else "Creditor",
        "FI_Fraud_Type": random.choice(["ID_THEFT", "SOCIAL_ENGINEERING", "ACCOUNT_TAKEOVER"]),
        "Non_ISO_Transaction_Receive_Dtm": random_time_str(),
        "OrgnlMsgId": base_txn.get("InstrId", base_txn.get("MsgId", str(random.randint(100000, 999999)))),
        "Rsn_Cd": "FRAUD",
        "SP_FraudFlag": 128,
        "SP_MessageTypeID": MTID
    }

def main():
    with open(INPUT_FILE, "r") as f:
        transactions = [json.loads(line) for line in f if line.strip()]
    
    total_chunks = len(transactions) // CHUNK_SIZE
    print(f"Total transactions: {len(transactions)} — Processing {total_chunks} chunks of 1000...")

    for i in range(0, len(transactions), CHUNK_SIZE):
        chunk = transactions[i:i+CHUNK_SIZE]
        if len(chunk) < FRAUDS_PER_CHUNK:
            continue  # skip small tail chunks

        selected = random.sample(chunk, FRAUDS_PER_CHUNK)
        for txn in selected:
            payload = generate_fraud_report(txn)
            response = requests.post(ENDPOINT, headers=HEADERS, json=payload)
            print("\nSubmitted Fraud Report:")
            print(json.dumps(payload, indent=2))
            print("Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                print(response.text)

if __name__ == "__main__":
    main()
