
# --- Script to grant qualification to Worker IDs for Ctrl Bias - Ethan Pablo

import boto3

# ---- Fill these in with your IAM keys ----
AWS_ACCESS_KEY_ID = "insert your access key"
AWS_SECRET_ACCESS_KEY = "Insert your secret key"

# ---- Replace with Sandbox QualificationTypeId you created ----
QUAL_TYPE_ID = ""

# ---- List of worker IDs for Ctrl Bias ----
WORKER_IDS = [

]

# ---- Create MTurk client pointing to Sandbox ----
client = boto3.client(
    "mturk",
    region_name="us-east-1",
    endpoint_url="https://mturk-requester-sandbox.us-east-1.amazonaws.com",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ---- Grant the qualification to each worker ----
for wid in WORKER_IDS:
    response = client.associate_qualification_with_worker(
        QualificationTypeId=QUAL_TYPE_ID,
        WorkerId=wid,
        IntegerValue=100,        # Score (100 = pass)
        SendNotification=True   
    )
    print(f"Granted qualification {QUAL_TYPE_ID} to worker {wid}")




