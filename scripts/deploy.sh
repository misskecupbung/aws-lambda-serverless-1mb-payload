#!/usr/bin/env bash
# Usage: ./deploy.sh [region]
set -euo pipefail

REGION=${1:-us-east-1}
STACK_NAME="lambda-1mb-payload"

echo "==> Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file cloudformation/template.yaml \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION" \
  --no-fail-on-empty-changeset

PRODUCER_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ProducerFunctionName'].OutputValue" \
  --output text)

CONSUMER_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ConsumerFunctionName'].OutputValue" \
  --output text)

echo "==> Packaging and pushing function code..."
cd lambda
zip -q producer-only.zip producer.py
zip -q consumer-only.zip consumer.py
cd ..

aws lambda update-function-code \
  --function-name "$PRODUCER_NAME" \
  --zip-file fileb://lambda/producer-only.zip \
  --region "$REGION" > /dev/null

aws lambda update-function-configuration \
  --function-name "$PRODUCER_NAME" \
  --handler producer.handler \
  --region "$REGION" > /dev/null

aws lambda update-function-code \
  --function-name "$CONSUMER_NAME" \
  --zip-file fileb://lambda/consumer-only.zip \
  --region "$REGION" > /dev/null

aws lambda update-function-configuration \
  --function-name "$CONSUMER_NAME" \
  --handler consumer.handler \
  --region "$REGION" > /dev/null

rm -f lambda/producer-only.zip lambda/consumer-only.zip

echo ""
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[*].{Key: OutputKey, Value: OutputValue}" \
  --output table
