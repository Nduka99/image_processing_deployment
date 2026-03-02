"""
AWS Lambda handler that wraps our FastAPI predict function.
Translates API Gateway v2 events into our ML prediction pipeline.
"""
import json
import base64
import cv2
import numpy as np
from api.dependencies import get_ml_pipeline
from api.feature_extractor import process_raw_image


def handler(event, context):
    """
    Lambda entry point. Handles:
      - POST /predict  → ML inference
      - GET  /health   → health check
    """
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")

    # Health check
    if path == "/health" and http_method == "GET":
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"status": "ok", "message": "ML Inference API is running."})
        }

    # Predict endpoint
    if path == "/predict" and http_method == "POST":
        try:
            # Decode the image from the multipart body
            body = event.get("body", "")
            is_base64 = event.get("isBase64Encoded", False)

            if is_base64:
                body_bytes = base64.b64decode(body)
            else:
                body_bytes = body.encode("latin-1") if isinstance(body, str) else body

            # Extract the file from multipart form data
            content_type = event.get("headers", {}).get("content-type", "")
            image_bytes = _extract_file_from_multipart(body_bytes, content_type)

            if image_bytes is None:
                return _error_response(400, "No image file found in request.")

            # Decode image with OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_bgr is None:
                return _error_response(400, "Could not decode image.")

            # Run the ML Pipeline
            pipeline = get_ml_pipeline()
            raw_features = process_raw_image(img_bgr)
            scaled_features = pipeline.preprocess(raw_features)
            outputs = pipeline.session.run(None, {pipeline.input_name: scaled_features})

            pred_label_idx = int(outputs[0][0])

            confidence = 1.0
            prob_cat = 0.0
            prob_dog = 0.0

            if len(outputs) > 1:
                try:
                    prob_array = outputs[1][0]
                    prob_cat = float(prob_array[0])
                    prob_dog = float(prob_array[1])
                    confidence = max(prob_cat, prob_dog)
                except Exception:
                    pass

            if confidence < 0.51:
                result = {
                    "success": True,
                    "prediction": "unknown",
                    "confidence": confidence,
                    "prob_cat": prob_cat,
                    "prob_dog": prob_dog,
                    "message": "Hmm... that doesn't look like a cat or a dog! Are you trying to trick me?"
                }
            else:
                label = "dog" if pred_label_idx == 1 else "cat"
                result = {
                    "success": True,
                    "prediction": label,
                    "confidence": confidence,
                    "prob_cat": prob_cat,
                    "prob_dog": prob_dog,
                    "message": "Prediction successful"
                }

            return {
                "statusCode": 200,
                "headers": _cors_headers(),
                "body": json.dumps(result)
            }

        except Exception as e:
            return _error_response(500, f"Inference error: {str(e)}")

    return _error_response(404, "Not found")


def _cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    }


def _error_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({"detail": message})
    }


def _extract_file_from_multipart(body_bytes, content_type):
    """Parse multipart/form-data to extract the uploaded file bytes."""
    if "multipart/form-data" not in content_type:
        # Assume raw image bytes
        return body_bytes

    # Extract boundary from content-type header
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[len("boundary="):].strip().encode()
            break

    if boundary is None:
        return None

    # Split body by boundary
    parts = body_bytes.split(b"--" + boundary)

    for part in parts:
        if b"filename=" in part:
            # Find the blank line separating headers from body
            header_end = part.find(b"\r\n\r\n")
            if header_end != -1:
                file_data = part[header_end + 4:]
                # Remove trailing \r\n-- or \r\n
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]
                if file_data.endswith(b"--"):
                    file_data = file_data[:-2]
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]
                return file_data

    return None
