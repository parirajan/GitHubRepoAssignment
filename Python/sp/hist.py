import random
import string
import uuid
import requests
from datetime import datetime, timedelta
import numpy as np
import json

# Configuration
N_FIS = 20
N_ACCOUNTS_PER_FI = 300
N_TRANSACTIONS = 1000
ENDPOINT = "http://localhost:8080/"
MTID = 1
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Generate FIs and Accounts
fi_list = ['FI' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(N_FIS)]
account_list = [
    {
        "IBAN": "IBAN" + ''.join(random.choices(string.digits, k=14)),
        "Name": "Acct_" + ''.join(random.choices(string.ascii_letters, k=6)),
        "BankID": fi
    }
    for fi in fi_list for _ in range(N_ACCOUNTS_PER_FI)
]

def random_account():
    return random.choice(account_list)

def random_datetime(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def generate_transaction():
    dt = random_datetime(datetime(2025, 1, 1), datetime(2025, 8, 5))
    debtor = random_account()
    creditor = random_account()
    amount = round(np.random.uniform(100, 100000), 2)
    msg_id = dt.strftime("%Y%m%d") + ''.join(random.choices(string.ascii_letters + string.digits, k=28))

    return {
        "CdtrAcct_Id_IBAN": creditor["IBAN"],
        "CdtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "CdtrAcct_Tp_Cd": "CACC",
        "CdtrAcct_Tp_Prtry": "SALA",
        "CdtrAgt_FinInstnId_ClrSysMmbId_MmbId": creditor["BankID"],
        "CdtrAgt_FinInstnId_Nm": creditor["BankID"] + "_BANK",
        "DbtrAcct_Id_IBAN": debtor["IBAN"],
        "DbtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "DbtrAcct_Tp_Cd": "CACC",
        "DbtrAcct_Tp_Prtry": "SALA",
        "DbtrAgt_FinInstnId_ClrSysMmbId_MmbId": debtor["BankID"],
        "DbtrAgt_FinInstnId_Nm": debtor["BankID"] + "_BANK",
        "IntrBkSttlmAmt": amount,
        "IntrBkSttlmAmt_@Ccy": "USD",
        "MsgId": msg_id,
        "PmtId_EndToEndId": str(uuid.uuid4()),
        "PmtId_TxId": str(uuid.uuid4()),
        "TxSts": "ACCP",
        "Non_ISO_transaction_type_cd": random.choice([
            "CUST_CREDIT_TRANSFER", "FI_CREDIT_TRANSFER", "INTRA_BANK_TRANSFER", "INTERNAL_TRANSFER"
        ]),
        "Non_ISO_Status_Cd": random.choice(["SETTLED", "REVERSED", "RETURNED", "REJECTED"]),
        "Non_receiver_response_cd": random.choice(["ACSC", "ACTC", "ACWP", "RJCT", "UNSET"]),
        "Non_ISO_Transaction_Receive_Dtm": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "SP_MessageTypeID": MTID,
        "TxDtTm": dt.strftime("%Y-%m-%dT%H:%M:%S")
    }

submitted_transactions = []

for i in range(N_TRANSACTIONS):
    payload = generate_transaction()
    submitted_transactions.append(payload)
    try:
        response = requests.post(ENDPOINT, json=payload, headers={"SP_MessageTypeID": str(MTID)})
        print(f"[{i+1}/{N_TRANSACTIONS}] {response.status_code} {response.text}")
    except Exception as e:
        print(f"[{i+1}/{N_TRANSACTIONS}] Exception: {str(e)}")

with open("mtid1_transactions.jsonl", "w") as f:
    for txn in submitted_transactions:
        f.write(json.dumps(txn) + "\n")
