import json
import random
import string
import requests
from datetime import datetime

MTID = 4
ENDPOINT = "http://localhost:8080/"
HISTORICAL_FILE = "mtid1_transactions.jsonl"

with open(HISTORICAL_FILE, "r") as f:
    transactions = [json.loads(line) for line in f if line.strip()]

prescreen_txns = random.sample(transactions, 50)

def random_msg_id():
    return datetime.now().strftime("%Y%m%d") + ''.join(random.choices(string.ascii_letters + string.digits, k=28))

for txn in prescreen_txns:
    payload = {
        "MsgId": random_msg_id(),
        "CdtrAcct_Id_IBAN": txn["CdtrAcct_Id_IBAN"],
        "DbtrAcct_Id_IBAN": txn["DbtrAcct_Id_IBAN"],
        "IntrBkSttlmAmt": txn["IntrBkSttlmAmt"],
        "IntrBkSttlmAmt_@Ccy": "USD",
        "TxDtTm": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "SP_MessageTypeID": MTID
    }
    requests.post(ENDPOINT, json=payload, headers={"SP_MessageTypeID": str(MTID)})
