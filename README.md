# AWS Lambda 1 MB Payload Size

Hands-on lab for the Lambda 1 MB async payload increase, launched January 2026.

AWS Lambda, SQS, and EventBridge now support payloads up to 1 MB for asynchronous invocations and messages — up from the previous 256 KB limit for Lambda async and EventBridge, and 256 KB for SQS. This removes a common architectural workaround: storing large payloads in S3 first, then passing only the S3 reference in the event.

## Architecture

## Prerequisites

- AWS CLI configured
- Python 3.12+
- IAM permissions: `lambda:*`, `sqs:*`, `events:*`, `iam:*`

## Deploy

```bash
cd aws-lambda-serverless-1mb-payload
./scripts/deploy.sh
```

## Test

```bash
./scripts/send-large-payload.sh
./scripts/read-result.sh
```

## Clean up

```bash
./scripts/cleanup.sh
```
