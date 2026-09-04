# Setup Steps

Follow these steps in order to configure the pipeline in your AWS account.

> **How automation works:** Instead of manually sending a message to SQS, we configure S3 to automatically send an event notification to the SQS queue whenever a file is uploaded to the `raw/` folder. This means uploading a file is the only action needed to trigger the entire pipeline.

---

## A. Create the SQS Queue

1. Go to **AWS Console → SQS → Create Queue**
2. Type: **Standard**
3. Name: `sales-pipeline-queue`
4. Leave all settings default → click **Create Queue**
5. Note the **Queue ARN** — you will need it in the next step (format: `arn:aws:sqs:us-east-1:<account-id>:sales-pipeline-queue`)

### Update the SQS Access Policy

By default SQS only accepts messages from the account owner. We need to allow S3 to send messages to it.

1. Open the queue → click **Edit** → scroll to **Access Policy**
2. Click **Policy Generator** and fill in the fields:

| Field        | Value                                                              |
| ------------ | ------------------------------------------------------------------ |
| Effect       | Allow                                                              |
| Principal(s) | `*`                                                                |
| Action(s)    | `sqs:*`                                                            |
| Resource(s)  | `arn:aws:sqs:us-east-1:<account-id>:sales-pipeline-queue`          |
| Condition    | ArnEquals → `aws:SourceArn` → `arn:aws:s3:::sales-data-bucket-sqs` |

3. Click **Generate Policy** → copy the JSON → paste it into the Access Policy field → click **Save**

> The `Principal *` allows any AWS service to write to this queue. The `Condition` locks it down so **only your S3 bucket** (`sales-data-bucket-sqs`) can actually send messages — nothing else can write to the queue.

---

## B. Create the S3 Bucket

1. Go to **AWS Console → S3 → Create Bucket**
2. Bucket name: `sales-data-bucket-sqs`
3. Region: **same region as your SQS queue** — this is required for S3 event notifications to work
4. Leave all other settings default → click **Create Bucket**
5. Open the bucket → **Create Folder** → name it `sales-data`
6. Inside `sales-data`, create two sub-folders: `raw` and `processed`

### Configure S3 Event Notification (automation step)

This is what automates the pipeline — S3 will send a message to SQS automatically every time a file is uploaded.

1. Open the bucket → go to the **Properties** tab → scroll to **Event Notifications**
2. Click **Create Event Notification**
3. Fill in the fields:

| Field       | Value                        |
| ----------- | ---------------------------- |
| Event name  | `sales-pipeline-trigger`     |
| Prefix      | `sales-data/raw/`            |
| Event type  | **All object create events** |
| Destination | SQS Queue                    |
| SQS Queue   | `sales-pipeline-queue`       |

4. Click **Save Changes**

> From this point on, uploading any file to `sales-data/raw/` will automatically send an S3 event to SQS — no manual message needed.

> **Note:** Because S3 sends its own event format, the Lambda function extracts `bucket` and `key` directly from the S3 event structure rather than reading a custom JSON message. The full Lambda code is in **Step E**.

---

## C. Create the IAM Role for Lambda

1. Go to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service** → Use case: **Lambda** → Next
3. Attach these policies:

| Policy                 | Purpose                             |
| ---------------------- | ----------------------------------- |
| `AmazonSQSFullAccess`  | Read and delete SQS messages        |
| `AmazonS3FullAccess`   | Read raw data, write processed data |
| `AWSGlueServiceRole`   | Start Glue jobs                     |
| `CloudWatchFullAccess` | Write Lambda logs                   |

4. Role name: `lambda-pipeline-role` → **Create Role**

---

## D. Create the AWS Glue Job

1. Go to **AWS Glue → ETL Jobs → Script Editor**
2. Engine: **Spark** → **Create**
3. Paste the Glue script below into the editor:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when, round as spark_round

args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 'file_name', 'source_path', 'destination_path', 'S3_BUCKET'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

source = f"s3://{args['S3_BUCKET']}/{args['source_path']}{args['file_name']}"
dest   = f"s3://{args['S3_BUCKET']}/{args['destination_path']}"

df = spark.read.option("header","true").option("inferSchema","true").csv(source)

df = df.withColumn("total_amount", spark_round(col("quantity") * col("price"), 2))
df = df.withColumn("order_size",
    when(col("total_amount") >= 500, "Large")
    .when(col("total_amount") >= 100, "Medium")
    .otherwise("Small"))

df_out = df.filter(col("status") == "Completed")
df_out.write.mode("overwrite").option("header","true").parquet(dest)

print("Done. Written to:", dest)
job.commit()
```

4. Job name: `sales-data-processor`
5. IAM Role: create/select a Glue service role with `AmazonS3FullAccess`
6. Click **Save**

---

## E. Create the Lambda Function

1. Go to **Lambda → Create Function → Author from scratch**
2. Function name: `sales-pipeline-trigger`
3. Runtime: **Python 3.12**
4. Execution role: Use existing → select `lambda-pipeline-role`
5. Click **Create Function**
6. In the **Code** tab, replace the default code with:

```python
import json
import boto3

glue = boto3.client('glue')

def lambda_handler(event, context):
    print('Full Event:', json.dumps(event))
    try:
        for record in event['Records']:
            # SQS message body contains the S3 event as JSON
            s3_event = json.loads(record['body'])

            # Handle S3 test event (sent when notification is first configured)
            if 'Event' in s3_event and s3_event['Event'] == 's3:TestEvent':
                print('Test Event Received')
            else:
                # Loop through S3 records inside the SQS message
                for s3_record in s3_event['Records']:
                    bucket_name = s3_record['s3']['bucket']['name']
                    object_key  = s3_record['s3']['object']['key']
                    file_name   = object_key.split('/')[-1]
                    source_path = '/'.join(object_key.split('/')[:-1]) + '/'

                    print('Bucket Name:', bucket_name)
                    print('Object Key:',  object_key)
                    print('File Name:',   file_name)
                    print('Source Path:', source_path)

                    # Trigger the Glue job with file details
                    response = glue.start_job_run(
                        JobName='sales-data-processor',
                        Arguments={
                            '--S3_BUCKET':        bucket_name,
                            '--file_name':        file_name,
                            '--source_path':      source_path,
                            '--destination_path': 'sales-data/processed/'
                        }
                    )
                    print('Glue Job Started. JobRunId:', response['JobRunId'])

        return {'statusCode': 200, 'body': 'Success'}
    except Exception as e:
        print('Error:', str(e))
        raise e
```

7. Click **Deploy**

### Add SQS Trigger

1. Click **Add Trigger** inside the Lambda function
2. Source: **SQS**
3. Queue: `sales-pipeline-queue`
4. Batch size: `1`
5. Click **Add**

---

## F. Verify All Resources

Before testing, confirm:

- S3 bucket has `sales-data/raw/sales_data.csv`
- SQS queue `sales-pipeline-queue` exists
- Lambda function has SQS trigger active
- Glue job `sales-data-processor` is saved and shows status _Ready_
- IAM role attached to Lambda includes all four policies

See `testing.md` for end-to-end verification.
