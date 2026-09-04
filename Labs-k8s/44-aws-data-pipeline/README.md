# AWS Event-Driven Data Processing Pipeline

## Objective

Design an event-driven data pipeline where a message sent to a queue triggers processing of a dataset stored in cloud storage. The pipeline processes the data and stores the transformed output in a separate location.

## Architecture

```
Data Request → SQS Queue → Lambda Trigger → Glue Job → Processed Data in S3
```

See `architecture-diagram.png` for the visual diagram.

## Services Used

- **Amazon SQS** — Receives the pipeline trigger message
- **AWS Lambda** — Triggered by SQS; starts the Glue job
- **AWS Glue** — Reads CSV, transforms data, writes output to S3
- **Amazon S3** — Stores raw input and processed output

## Project Structure

```
aws-event-driven-pipeline/
├── README.md
├── architecture-diagram.png
├── data/
│   ├── sample_output
│   │   └── sample.parquet
│   └── sales_data.csv
├── documentation/
│   ├── architecture.md
│   ├── setup_steps.md
│   └── testing.md
└── screenshots/
    ├── setup
    └── Testing
```

## Sample SQS Message

```json
{
  "file_name": "sales_data.csv",
  "source_path": "sales-data/raw/",
  "destination_path": "sales-data/processed/"
}
```

## S3 Folder Structure

```
sales-data/
  raw/
    sales_data.csv
  processed/
```

## Lambda Responsibility

1. Receive message from SQS
2. Extract file details
3. Trigger Glue job

## Glue Job Responsibility

1. Read CSV from S3
2. Perform transformations
3. Store output in processed folder

## Setup

See `documentation/setup_steps.md` for full step-by-step instructions.

## Testing

See `documentation/testing.md` for verification steps.

## Deliverables

1. Architecture diagram (`architecture-diagram.png`)
2. Screenshots of AWS resources (`screenshots/`)
3. Pipeline workflow explanation (`documentation/architecture.md`)
4. Sample SQS message (see above)
5. Output data screenshot (`screenshots/Testing/s3_output.png`)
