#!/usr/bin/env bash
# Usage: ./cleanup.sh [region]
set -euo pipefail

REGION=${1:-us-east-1}
STACK_NAME="lambda-1mb-payload"

echo "==> Deleting stack: $STACK_NAME"
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo "Done."
