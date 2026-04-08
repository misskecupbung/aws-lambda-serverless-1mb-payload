#!/usr/bin/env bash
# Usage: ./read-result.sh [region]
set -euo pipefail

REGION=${1:-us-east-1}

aws logs tail /aws/lambda/large-payload-consumer \
  --since 15m \
  --region "$REGION" \
  --format short | grep -E "Received|ERROR" | tail -20
