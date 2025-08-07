import json
import random
import string
import requests
from datetime import datetime

MTID = 2
ENDPOINT = "http://localhost:8080/"
HISTORICAL_FILE = "mtid1_transactions.jsonl"
N_CAMT = 5
N_PAIN = 5
random.seed(42)

with open(HISTORICAL_FILE, "r") as f:
    transactions = [json.loads(line) for line in f if line.strip()]

camt_count = int((len(transactions) / 100) * N_CAMT)
pain_count = int((len(transactions) / 100) * N_PAIN)

selected_camt = random.sample(transactions, camt_count)
selected_pain = random.sample(transactions, pain_count)
fraud_candidates = selected_camt + selected_pain

def random_msg_id():
    return datetime.now().strftime("%Y%m%d") + ''.join(random.choices(string.ascii_letters + string.digits, k=28))

for txn in selected_camt:
    payload = {
        "MsgId": random_msg_id(),
        "OrgnlMsgId": txn["MsgId"],
        "TxSts": "RJCT",
        "Rsn_Cd": "NARRATIVE",
        "AddtlInf": "Rejected after post-settlement validation",
        "SP_MessageTypeID": MTID
    }
    requests.post(ENDPOINT, json=payload, headers={"SP_MessageTypeID": str(MTID)})

for txn in selected_pain:
    payload = {
        "MsgId": random_msg_id(),
        "OrgnlMsgId": txn["MsgId"],
        "TxSts": "ACSC",
        "Rsn_Cd": "AM04",
        "AddtlInf": "Duplicate settlement request",
        "SP_MessageTypeID": MTID
    }
    requests.post(ENDPOINT, json=payload, headers={"SP_MessageTypeID": str(MTID)})

with open("fraud_candidates.jsonl", "w") as f:
    for tx in fraud_candidates:
        f.write(json.dumps(tx) + "\n")
