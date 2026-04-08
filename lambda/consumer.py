import json
import logging
import sys

logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context):
    """
    Consumer function — logs the size of each received payload.
    Handles async Lambda invocations and SQS event source mapping.
    Also invoked by EventBridge rule.
    """
    # SQS event source mapping wraps messages in a Records list.
    if "Records" in event:
        for record in event["Records"]:
            if record.get("eventSource") == "aws:sqs":
                body = json.loads(record["body"])
                payload_bytes = len(record["body"].encode())
                source = body.get("source", "sqs")
                logger.info(
                    "Received SQS message from %s: %.1f KB", source, payload_bytes / 1024
                )
        return {"status": "ok", "source": "sqs"}

    # EventBridge event — has "source" and "detail" fields.
    if event.get("source") == "lab.producer":
        detail = event.get("detail", {})
        detail_bytes = len(json.dumps(detail).encode())
        logger.info(
            "Received EventBridge event: %.1f KB in detail field", detail_bytes / 1024
        )
        return {"status": "ok", "source": "eventbridge", "detail_kb": round(detail_bytes / 1024, 1)}

    # Direct async Lambda invocation.
    payload_bytes = len(json.dumps(event).encode())
    logger.info(
        "Received async invocation: %.1f KB total payload", payload_bytes / 1024
    )
    return {
        "status": "ok",
        "source": event.get("source", "async-invoke"),
        "size_kb": round(payload_bytes / 1024, 1),
    }
