import base64
import json
import logging
import os
from urllib.parse import parse_qs


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_ORIGIN = os.environ.get("CORS_ALLOW_ORIGIN", "*")


def _build_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }


def handler(event, context):  # AWS Lambda entrypoint
    if event.get("httpMethod") == "OPTIONS":
        return _build_response(200, {})

    try:
        raw_body = event.get("body") or ""
        if event.get("isBase64Encoded"):
            raw_body = base64.b64decode(raw_body).decode("utf-8")

        headers = event.get("headers") or {}
        content_type = headers.get("content-type") or headers.get("Content-Type") or ""

        data: dict = {}

        if "application/json" in content_type:
            if raw_body:
                data = json.loads(raw_body)
        elif "application/x-www-form-urlencoded" in content_type:
            parsed = parse_qs(raw_body)
            data = {k: v[0] for k, v in parsed.items()}
        else:
            if raw_body:
                try:
                    data = json.loads(raw_body)
                except Exception:
                    parsed = parse_qs(raw_body)
                    data = {k: v[0] for k, v in parsed.items()}

        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()

        if not name or not phone:
            return _build_response(
                400,
                {"message": "Both 'name' and 'phone' are required."},
            )

        request_id = getattr(context, "aws_request_id", "unknown")

        logger.info(
            "Landing form submission",
            extra={"name": name, "phone": phone, "request_id": request_id},
        )

        return _build_response(200, {"message": "Form submitted"})
    except Exception:
        logger.exception("Error handling form submission")
        return _build_response(500, {"message": "Internal server error"})
