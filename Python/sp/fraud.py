import json
import random
import string
import requests
from datetime import datetime

MTID = 3
ENDPOINT = "http://localhost:8080/"
FRAUD_FILE = "fraud_candidates.jsonl"

with open(FRAUD_FILE, "r") as f:
    candidates = [json.loads(line) for line in f if line.strip()]

frauds = random.sample(candidates, max(3, len(candidates) // 1000 * 3))

def random_msg_id():
    return datetime.now().strftime("%Y%m%d") + ''.join(random.choices(string.ascii_letters + string.digits, k=28))

for txn in frauds:
    payload = {
        "MsgId": random_msg_id(),
        "OrgnlMsgId": txn["MsgId"],
        "TxSts": "FRAD",
        "FraudType": "Reported",
        "AddtlInf": "Customer-initiated fraud report",
        "SP_MessageTypeID": MTID
    }
    requests.post(ENDPOINT, json=payload, headers={"SP_MessageTypeID": str(MTID)})
