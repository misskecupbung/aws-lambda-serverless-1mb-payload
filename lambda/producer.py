import boto3
import json
import logging
import os
import random
import string
import sys

logger = logging.getLogger()
logger.setLevel("INFO")

lambda_client = boto3.client("lambda")
sqs_client = boto3.client("sqs")
events_client = boto3.client("events")


def _generate_payload(target_kb: int) -> dict:
    """Generate a dict with a data field sized to approximately target_kb."""
    # Each character in the data string is ~1 byte in JSON encoding.
    target_bytes = target_kb * 1024
    # Reserve ~200 bytes for the surrounding JSON structure.
    data_len = max(0, target_bytes - 200)
    data = "".join(random.choices(string.ascii_lowercase + string.digits, k=data_len))
    return {
        "source": "lab.producer",
        "description": f"Generated {target_kb}KB test payload",
        "data": data,
    }


def handler(event, context):
    consumer_arn = os.environ["CONSUMER_FUNCTION_ARN"]
    queue_url = os.environ["SQS_QUEUE_URL"]
    event_bus_name = os.environ["EVENT_BUS_NAME"]

    mode = event.get("mode", "all")  # "async", "sqs", "eventbridge", or "all"
    payload_kb = int(event.get("payload_kb", 900))

    results = {}

    # Path 1: Async Lambda invocation (up to 1 MB)
    if mode in ("async", "all"):
        payload = _generate_payload(payload_kb)
        payload["source"] = "async-invoke"
        payload_bytes = json.dumps(payload).encode()
        logger.info("Async invocation payload size: %.1f KB", len(payload_bytes) / 1024)
        resp = lambda_client.invoke(
            FunctionName=consumer_arn,
            InvocationType="Event",  # async
            Payload=payload_bytes,
        )
        results["async_invoke"] = {
            "status_code": resp["StatusCode"],
            "payload_kb": round(len(payload_bytes) / 1024, 1),
        }
        logger.info("Async invoke: %s", results["async_invoke"])

    # Path 2: SQS message (up to 1 MB)
    if mode in ("sqs", "all"):
        payload = _generate_payload(payload_kb)
        payload["source"] = "sqs"
        message_body = json.dumps(payload)
        logger.info("SQS message size: %.1f KB", len(message_body.encode()) / 1024)
        resp = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
        )
        results["sqs"] = {
            "message_id": resp["MessageId"],
            "payload_kb": round(len(message_body.encode()) / 1024, 1),
        }
        logger.info("SQS send: %s", results["sqs"])

    # Path 3: EventBridge event (up to 1 MB for custom buses)
    if mode in ("eventbridge", "all"):
        # EventBridge 1 MB limit applies to the total event envelope.
        # The detail field holds the payload.
        payload = _generate_payload(min(payload_kb, 700))  # envelope overhead
        payload["source"] = "eventbridge"
        detail_str = json.dumps(payload)
        logger.info("EventBridge detail size: %.1f KB", len(detail_str.encode()) / 1024)
        resp = events_client.put_events(
            Entries=[{
                "Source": "lab.producer",
                "DetailType": "LargePayloadEvent",
                "Detail": detail_str,
                "EventBusName": event_bus_name,
            }]
        )
        results["eventbridge"] = {
            "failed_entry_count": resp["FailedEntryCount"],
            "payload_kb": round(len(detail_str.encode()) / 1024, 1),
        }
        logger.info("EventBridge put: %s", results["eventbridge"])

    return {"status": "ok", "results": results}
