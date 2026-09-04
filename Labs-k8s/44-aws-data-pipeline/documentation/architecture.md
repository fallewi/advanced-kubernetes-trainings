# Architecture — AWS Event-Driven Data Processing Pipeline

## Overview

This pipeline is fully serverless and event-driven. No infrastructure is provisioned manually — each component wakes up automatically when triggered by the previous one.

## Data Flow

```
Developer sends JSON message
          │
          ▼
    Amazon SQS Queue
    (sales-pipeline-queue)
          │
          │  SQS event trigger
          ▼
    AWS Lambda Function
    (sales-pipeline-trigger)
          │
          │  boto3: start_job_run()
          ▼
    AWS Glue ETL Job
    (sales-data-processor)
       │         │
  reads from   writes to
       │         │
       ▼         ▼
   S3 raw/   S3 processed/
```

## Component Roles

### Amazon SQS

- Entry point to the pipeline
- Receives a JSON message with `file_name`, `source_path`, `destination_path`
- Retains the message if Lambda is unavailable (decoupling)
- Queue type: Standard (at-least-once delivery)

### AWS Lambda

- Triggered automatically by SQS
- Parses the message body to extract file details
- Calls `glue_client.start_job_run()` passing paths as job arguments
- Runtime: Python 3.12

### AWS Glue

- Managed PySpark ETL job — no cluster management needed
- Reads `sales_data.csv` from `s3://<bucket>/sales-data/raw/`
- Applies transformations (see below)
- Writes Parquet output to `s3://<bucket>/sales-data/processed/`

### Amazon S3

- `raw/` — holds the original CSV uploaded by the user
- `processed/` — receives Glue's transformed Parquet output

## Glue Transformations

| Transformation  | Description                                           |
| --------------- | ----------------------------------------------------- |
| `total_amount`  | New column: `quantity × price`                        |
| `order_size`    | New column: Large (≥500), Medium (≥100), Small (<100) |
| Status clean-up | Standardise capitalisation of `status` field          |
| Filter          | Keep only `Completed` orders in output                |

## IAM Roles

| Role                   | Attached Policies                                             |
| ---------------------- | ------------------------------------------------------------- |
| `lambda-pipeline-role` | AmazonSQSFullAccess, AWSGlueServiceRole, CloudWatchFullAccess |
| Glue service role      | AmazonS3FullAccess, AWSGlueServiceRole, CloudWatchFullAccess  |

## Why These Design Choices?

- **SQS as entry point** — decouples the trigger from processing; messages persist if downstream is busy
- **Lambda for orchestration** — lightweight, zero infrastructure, ideal for passing a message and starting a job
- **Glue for ETL** — handles large files using managed Spark; no server provisioning needed
- **Parquet output** — columnar format; efficient for analytics with Athena or QuickSight
