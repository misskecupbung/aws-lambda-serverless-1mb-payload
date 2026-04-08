# AWS Lambda 1 MB Payload Size

Hands-on lab for the Lambda 1 MB async payload increase, launched January 2026.

AWS Lambda, SQS, and EventBridge now support payloads up to 1 MB for asynchronous invocations and messages — up from the previous 256 KB limit for Lambda async and EventBridge, and 256 KB for SQS. This removes a common architectural workaround: storing large payloads in S3 first, then passing only the S3 reference in the event.

## Prerequisites

- AWS CLI configured
- Python 3.12+
- IAM permissions: `lambda:*`, `sqs:*`, `events:*`, `iam:*`

## Deploy

```bash
REGION=us-east-1
STACK_NAME="lambda-1mb-payload"

aws cloudformation deploy \
  --template-file cloudformation/template.yaml \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"

PRODUCER=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ProducerFunctionName'].OutputValue" \
  --output text)

CONSUMER=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ConsumerFunctionName'].OutputValue" \
  --output text)

cd lambda && zip -q producer-only.zip producer.py && zip -q consumer-only.zip consumer.py && cd ..

aws lambda update-function-code \
  --function-name "$PRODUCER" --zip-file fileb://lambda/producer-only.zip --region "$REGION"
aws lambda update-function-code \
  --function-name "$CONSUMER" --zip-file fileb://lambda/consumer-only.zip --region "$REGION"
```

## Send large payloads

```bash
# Async Lambda invocation (900 KB)
aws lambda invoke \
  --function-name "$PRODUCER" \
  --payload '{"mode": "async", "payload_kb": 900}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" out.json && python3 -m json.tool out.json

# SQS (900 KB)
aws lambda invoke \
  --function-name "$PRODUCER" \
  --payload '{"mode": "sqs", "payload_kb": 900}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" out.json && python3 -m json.tool out.json

# EventBridge (700 KB)
aws lambda invoke \
  --function-name "$PRODUCER" \
  --payload '{"mode": "eventbridge", "payload_kb": 700}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" out.json && python3 -m json.tool out.json
```

## Verify the consumer received the payloads

```bash
aws logs tail /aws/lambda/large-payload-consumer \
  --since 15m --region "$REGION" --format short | grep -E "Received|ERROR"
```

## Clean up

```bash
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
```
