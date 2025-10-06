# ===========================================================
# SageMaker: Scan S3 Parquet Files → Train XGBoost Model
# ===========================================================

# Install dependencies if needed
# (Skip this if running in SageMaker Studio/Notebook Instance)
# !pip install -q boto3 sagemaker pandas pyarrow scikit-learn s3fs

import boto3, os, pandas as pd, sagemaker
from sagemaker import image_uris, Session
from sagemaker.inputs import TrainingInput
from sklearn.model_selection import train_test_split

# ---- USER CONFIG ----
BUCKET = "YOUR-BUCKET-NAME"           # <-- change this
RAW_PREFIX = "path/to/raw"            # <-- Parquet folder
PREP_PREFIX = "path/to/prepared"
OUTPUT_PREFIX = "path/to/output"

LABEL_COLUMN = "label"                # <-- your target column
DROP_COLUMNS = []                     # columns to drop before training
OBJECTIVE = "binary:logistic"         # or "reg:squarederror"
INSTANCE_TYPE = "ml.m5.large"
INSTANCE_COUNT = 1

try:
    from sagemaker import get_execution_role
    ROLE = get_execution_role()
except Exception:
    ROLE = "arn:aws:iam::<ACCOUNT_ID>:role/<SageMakerExecutionRole>"  # Replace if needed

REGION = boto3.session.Session().region_name
s3 = boto3.client("s3", region_name=REGION)
sm_sess = Session()

print("Region:", REGION)
print("Role:", ROLE)
print("Bucket:", BUCKET)


def list_parquet_files(bucket, prefix):
    keys = []
    token = None
    while True:
        args = {"Bucket": bucket, "Prefix": prefix}
        if token:
            args["ContinuationToken"] = token
        resp = s3.list_objects_v2(**args)
        for obj in resp.get("Contents", []):
            if obj["Key"].lower().endswith(".parquet"):
                keys.append(obj["Key"])
        token = resp.get("NextContinuationToken")
        if not token:
            break
    return keys

files = list_parquet_files(BUCKET, RAW_PREFIX)
print(f"Found {len(files)} parquet files under s3://{BUCKET}/{RAW_PREFIX}")
for f in files[:10]:
    print(" •", f)



dfs = []
for k in files:
    path = f"s3://{BUCKET}/{k}"
    try:
        df_part = pd.read_parquet(path, storage_options={"anon": False})
        dfs.append(df_part)
    except Exception as e:
        print(f"Skipping {path} →", e)

if not dfs:
    raise ValueError("No parquet files loaded. Check your S3 path & permissions.")

df = pd.concat(dfs, ignore_index=True)
print("Combined dataframe shape:", df.shape)
display(df.head())

# Clean
if DROP_COLUMNS:
    df = df[[c for c in df.columns if c not in set(DROP_COLUMNS)]]

if LABEL_COLUMN not in df.columns:
    raise ValueError(f"Label column '{LABEL_COLUMN}' not found!")

cols = [LABEL_COLUMN] + [c for c in df.columns if c != LABEL_COLUMN]
df = df[cols]

# Split
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, shuffle=True)
train_df.to_csv("/tmp/train.csv", header=False, index=False)
val_df.to_csv("/tmp/validation.csv", header=False, index=False)

train_s3 = sm_sess.upload_data("/tmp/train.csv", bucket=BUCKET, key_prefix=f"{PREP_PREFIX}/train")
val_s3   = sm_sess.upload_data("/tmp/validation.csv", bucket=BUCKET, key_prefix=f"{PREP_PREFIX}/val")

print("Uploaded train:", train_s3)
print("Uploaded val:", val_s3)



xgb_image = image_uris.retrieve(framework="xgboost", region=REGION, version="1.7-1")

estimator = sagemaker.estimator.Estimator(
    image_uri=xgb_image,
    role=ROLE,
    instance_count=INSTANCE_COUNT,
    instance_type=INSTANCE_TYPE,
    output_path=f"s3://{BUCKET}/{OUTPUT_PREFIX}/",
    sagemaker_session=sm_sess,
)

hyperparams = {
    "objective": OBJECTIVE,
    "num_round": 100,
    "max_depth": 5,
    "eta": 0.2,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "auc" if OBJECTIVE.startswith("binary") else "rmse",
}
estimator.set_hyperparameters(**hyperparams)

train_input = TrainingInput(train_s3, content_type="text/csv")
val_input   = TrainingInput(val_s3, content_type="text/csv")

estimator.fit({"train": train_input, "validation": val_input}, wait=True)
print("Model artifact:", estimator.model_data)


