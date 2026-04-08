#!/usr/bin/env bash
# Usage: ./send-large-payload.sh [region]
# Set PAYLOAD_KB env var to change payload size (default 900).
set -euo pipefail

REGION=${1:-us-east-1}
STACK_NAME="lambda-1mb-payload"
PAYLOAD_KB="${PAYLOAD_KB:-900}"

PRODUCER_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ProducerFunctionName'].OutputValue" \
  --output text)

echo "==> Test 1: async Lambda invocation (${PAYLOAD_KB} KB)"
aws lambda invoke \
  --function-name "$PRODUCER_NAME" \
  --payload "{\"mode\": \"async\", \"payload_kb\": ${PAYLOAD_KB}}" \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  out.json > /dev/null
cat out.json | python3 -m json.tool

echo ""
echo "==> Test 2: SQS message (${PAYLOAD_KB} KB)"
aws lambda invoke \
  --function-name "$PRODUCER_NAME" \
  --payload "{\"mode\": \"sqs\", \"payload_kb\": ${PAYLOAD_KB}}" \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  out.json > /dev/null
cat out.json | python3 -m json.tool

echo ""
echo "==> Test 3: EventBridge event (700 KB)"
aws lambda invoke \
  --function-name "$PRODUCER_NAME" \
  --payload '{"mode": "eventbridge", "payload_kb": 700}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  out.json > /dev/null
cat out.json | python3 -m json.tool

rm -f out.json

echo ""
echo "Check consumer logs:"
echo "  aws logs tail /aws/lambda/large-payload-consumer --follow --region $REGION"
