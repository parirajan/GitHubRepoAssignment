
# 📄 Architecture & Security Plan: Phase 1
**Title**: Secure ML Model Development in SageMaker using Cross-Account S3 Parquet Data  
**Environment**: AWS GovCloud (US)  
**Phase**: 1 (Direct Parquet S3 Access, No Athena/Glue)

---

## ✅ Objective

To enable data scientists to securely develop and train machine learning models using **AWS SageMaker Notebooks** in **Account B (ML Platform)** by reading **Parquet-formatted data stored in S3** in **Account A (Data Lake)**.

This phase avoids use of Athena or Glue Catalog for simplified access and minimal exposure.

---

## 🧱 Architecture Diagram

```
┌──────────────────────────┐              ┌────────────────────────────┐
│   Account A: Data Lake   │              │     Account B: ML Platform │
│                          │              │                            │
│ - S3 Bucket (Parquet)    │  <---------- │ - SageMaker Notebook       │
│ - Bucket Policy          │     Read     │ - IAM Execution Role       │
└──────────────────────────┘              │ - Model output to S3 (B)   │
                                          └────────────────────────────┘
```

---

## 🔐 Security Model

| Area                     | Detail                                                                 |
|--------------------------|------------------------------------------------------------------------|
| **Data Source**          | S3 bucket in Account A with `s3:GetObject` permission for B's role      |
| **Data Access**          | Read-only using Pandas or PyArrow from notebook                        |
| **Data at Rest**         | KMS-encrypted in Account A                                              |
| **Model Output**         | Written to scoped S3 bucket in Account B                               |
| **IAM Trust**            | Role-based with cross-account trust policy                             |
| **User Access**          | Federated via Okta → IAM (IAM role trust for SageMaker)                |
| **Audit Logging**        | CloudTrail enabled on both accounts                                    |
| **Network Isolation**    | Private subnet, no internet access for notebook                        |
| **Lifecycle Hardening**  | Read-only FS outside `/home/SageMaker`; tools like curl/wget removed   |
| **Export Control**       | No file export/upload beyond S3 model output location                  |

---

## 🔧 Implementation Steps

### 📍 Account A (Data Lake)
1. Store Parquet data in `s3://settled-data-bucket/parquet/...`
2. Create S3 bucket policy:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws-us-gov:iam::<AccountB_ID>:role/SageMakerExecutionRole"
  },
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws-us-gov:s3:::settled-data-bucket/*"
}
```
3. (Optional) Add KMS key policy to allow decryption from B's role.

---

### 📍 Account B (SageMaker/ML)
1. Create `SageMakerExecutionRole` with policies:
   - `s3:GetObject` on Account A bucket
   - `s3:PutObject` on Account B model output bucket
2. Launch SageMaker Notebook in:
   - Private VPC subnet
   - Attached hardened lifecycle configuration
3. Enforce lifecycle config:
   - Remove `curl`, `wget`, `scp`
   - Lock `/` to read-only
   - Only write access to `/home/ec2-user/SageMaker`
4. Restrict access:
   - Notebook IAM user mapped from Okta
   - Allow only named users to launch/access notebooks via role/session tag

---

## 💻 Notebook Code Examples

**Load Parquet file from S3:**
```python
import pandas as pd
df = pd.read_parquet("s3://settled-data-bucket/parquet/2024/07/txns.parquet")
```

**Train a model:**
```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier().fit(X_train, y_train)
```

**Save model back to S3:**
```python
import boto3
import joblib

joblib.dump(model, "model.pkl")
s3 = boto3.client("s3")
s3.upload_file("model.pkl", "ml-models-accountb", "outputs/model.pkl")
```

---

## ✅ Benefits

| Benefit                  | Description                                        |
|--------------------------|----------------------------------------------------|
| **Zero data duplication**| No ETL or copy – read S3 data in-place             |
| **No Glue or Athena**    | Simpler permissions and configuration              |
| **Secured model output** | Models pushed only to controlled Account B S3      |
| **Private networking**   | SageMaker operates fully within GovCloud VPC       |
| **Auditable**            | All activities are traceable via CloudTrail        |

---

## 🔒 Compliance Highlights

- No public or internet access
- Controlled export (no `scp`, `wget`, `curl`, etc.)
- Notebook file system hardened
- Cross-account S3 access with scoped IAM role
- Data in encrypted S3 with audit trails

---

## 📌 Approval Request

Security team is requested to approve:
- Cross-account access to S3 Parquet (read-only)
- SageMaker notebook with hardened lifecycle config
- Federated IAM controls via Okta for user access
- Controlled model output back to Account B's S3 bucket

---
