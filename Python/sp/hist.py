import os
import uuid
import random
import json
import requests
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

API_URL = "http://localhost:8080/"
ACCOUNT_CSV_PATH = "200_accounts.csv"
LOG_PATH = "mtid1_transactions.jsonl"
NUM_TRANSACTIONS = 100
CURRENCY = "USD"
fake = Faker()

# Load or create 200 accounts
def generate_iban():
    return f"DE{random.randint(10, 99)}{random.randint(10000000, 99999999)}{random.randint(1000000000, 9999999999)}"

def generate_accounts_csv(filename=ACCOUNT_CSV_PATH, count=200):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    
    records = []
    for _ in range(count):
        records.append({
            "AccountID": str(uuid.uuid4()),
            "Name": fake.name(),
            "IBAN": generate_iban(),
            "BankID": random.randint(10000, 99999)
        })

    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    print(f"Created {filename} with {count} accounts.")
    return df

def fake_address(prefix):
    return {
        f"{prefix}_PstlAdr_BldgNm": "Building A",
        f"{prefix}_PstlAdr_StrtNm": "Main Street",
        f"{prefix}_PstlAdr_PstCd": "12345",
        f"{prefix}_PstlAdr_TwnNm": "Townsville",
        f"{prefix}_PstlAdr_Ctry": "US",
        f"{prefix}_PstlAdr_AdrLine": "123 Main Street",
        f"{prefix}_PstlAdr_Dept": "Finance",
        f"{prefix}_PstlAdr_SubDept": "Operations",
        f"{prefix}_PstlAdr_Room": "101",
        f"{prefix}_PstlAdr_Flr": "1",
        f"{prefix}_PstlAdr_BldgNb": "10",
        f"{prefix}_PstlAdr_DstrctNm": "Central",
        f"{prefix}_PstlAdr_CtrySubDvsn": "CA"
    }

def generate_full_historical_payload(creditor, debtor, date):
    amount = round(random.uniform(100.0, 100000.0), 2)
    return {
        "InstrId": str(uuid.uuid4()),
        "EndToEndId": str(uuid.uuid4()),
        "UETR": str(uuid.uuid4()),
        "CdtrAcct_Id_IBAN": creditor["IBAN"],
        "CdtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "CdtrAcct_Prxy_Id": str(uuid.uuid4()),
        "CdtrAcct_Tp_Cd": "CACC",
        "CdtrAcct_Tp_Prtry": "SAVINGS",
        "CdtrAgt_FinInstnId_ClrSysMmbId_MmbId": int(creditor["BankID"]),
        "Cdtr_Pty_Nm": creditor["Name"],
        **fake_address("Cdtr_Pty"),
        "DbtrAcct_Id_IBAN": debtor["IBAN"],
        "DbtrAcct_Id_Othr_Id": str(uuid.uuid4()),
        "DbtrAcct_Prxy_Id": str(uuid.uuid4()),
        "DbtrAcct_Tp_Cd": "CACC",
        "DbtrAcct_Tp_Prtry": "CHECKING",
        "DbtrAgt_FinInstnId_ClrSysMmbId_MmbId": int(debtor["BankID"]),
        "Dbtr_Pty_Nm": debtor["Name"],
        **fake_address("Dbtr_Pty"),
        "IntrBkSttlmAmt": amount,
        "IntrBkSttlmAmt_@Ccy": CURRENCY,
        "IntrBkSttlmDt": date.strftime("%Y-%m-%d"),
        "TxTp": "TRF",
        "TxSts": "ACTC",
        "TxId": str(uuid.uuid4()),
        "UpldDtTm": date.strftime("%Y-%m-%d %H:%M:%S"),
        "RgltryRptg_Dt": date.strftime("%Y-%m-%d"),
        "SP_FraudFlag": 0,
        "TxPrcDtTm": date.strftime("%Y-%m-%d %H:%M:%S")
    }

def append_to_transaction_log(payload, log_path=LOG_PATH):
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif hasattr(obj, "item"):
            return obj.item()
        return obj
    with open(log_path, "a") as f:
        f.write(json.dumps(convert(payload)) + "\n")

def post_historical_transactions(df, count=NUM_TRANSACTIONS):
    today = datetime.today()
    for i in range(count):
        creditor = df.sample().iloc[0]
        debtor = df.sample().iloc[0]
        while creditor["IBAN"] == debtor["IBAN"]:
            debtor = df.sample().iloc[0]
        date = today - timedelta(days=random.randint(1, 90))
        payload = generate_full_historical_payload(creditor, debtor, date)

        headers = {
            "Content-Type": "application/json",
            "SP_MessageTypeID": "1"
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            append_to_transaction_log(payload)
            print(f"\n[{i+1}/{count}] Response Status: {response.status_code}")
            print("Payload Sent:")
            print(json.dumps(payload, indent=2))
            print("Response Body:")
            try:
                print(json.dumps(response.json(), indent=2))
            except ValueError:
                print(response.text)
            print("-" * 80)
        except Exception as e:
            print(f"[{i+1}/{count}] Error: {e}")

if __name__ == "__main__":
    df = generate_accounts_csv()
    post_historical_transactions(df)
