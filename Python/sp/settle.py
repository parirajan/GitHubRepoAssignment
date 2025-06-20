import json
import uuid
import random
import requests
from datetime import datetime

API_URL = "http://localhost:8080/"
MTID_HEADER = "2"
LOG_FILE = "mtid1_transactions.jsonl"

def load_mtid1_transactions():
    with open(LOG_FILE, "r") as f:
        return [json.loads(line) for line in f.readlines()]

def generate_event(original, event_type):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "MsgId": str(uuid.uuid4()),
        "CreDtTm": now,
        "OrgnlInstrId": original["InstrId"],
        "OrgnlEndToEndId": original["EndToEndId"],
        "OrgnlUETR": original["UETR"],
        "OrgnlTxId": original.get("TxId", str(uuid.uuid4())),
        "OrgnlIntrBkSttlmAmt": original["IntrBkSttlmAmt"],
        "OrgnlIntrBkSttlmAmt_@Ccy": original["IntrBkSttlmAmt_@Ccy"],
        "OrgnlCreDtTm": original.get("UpldDtTm", now),
        "OrgnlMsgId": original.get("InstrId", str(uuid.uuid4())),
        "OrgnlMsgNmId": event_type,
        "CxlRsnInf_AddtlInf": f"{event_type} generated automatically",
        "Rsn_Cd": random.choice(["AC04", "AG01", "MD06", "MS03"]),
        "TrxSts": random.choice(["RJCT", "CANC"]),
        "SP_FraudFlag": random.choice([0, 1]),
        "Non_ISO_transaction_type_cd": event_type,
        "Non_ISO_transaction_Receive_Dtm": now,
        "Non_ISO_API_Version": 1
    }

def post_event(event):
    headers = {
        "Content-Type": "application/json",
        "SP_MessageTypeID": MTID_HEADER
    }
    try:
        response = requests.post(API_URL, json=event, headers=headers)
        print(f"Posted {event['Non_ISO_transaction_type_cd']} | Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    except Exception as e:
        print(f"Failed to post event: {e}")

def run_post_settlement():
    transactions = load_mtid1_transactions()
    chunk_size = 100

    for i in range(0, len(transactions), chunk_size):
        chunk = transactions[i:i + chunk_size]
        if len(chunk) < 10:
            continue  # Skip partial chunks

        selected_camt = random.sample(chunk, 5)
        selected_pain = random.sample(chunk, 5)

        for tx in selected_camt:
            event = generate_event(tx, "camt.056")
            post_event(event)

        for tx in selected_pain:
            event = generate_event(tx, "pain.014")
            post_event(event)

if __name__ == "__main__":
    run_post_settlement()
