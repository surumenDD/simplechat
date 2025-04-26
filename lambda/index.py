# lambda/index.py
import json, os, urllib.request, urllib.error, socket, logging


FASTAPI_BASE = os.environ.get(
    "FASTAPI_URL",                # 環境変数がなければ直書き URL を fallback
    "https://a45c-35-233-187-0.ngrok-free.app"
).rstrip("/")

def call_fastapi(message: str, timeout: int = 45) -> str:
    """FastAPI の /generate エンドポイントに JSON を POST して応答文字列を返す"""
    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        url=f"{FASTAPI_BASE}/generate",          # ★ FastAPI 側と同じパスに合わせる
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["response"]
    except urllib.error.HTTPError as e:
        # 4xx/5xx はここに来る（405, 404, 500 など）
        logging.error("FastAPI HTTPError %s %s", e.code, e.reason)
        raise
    except (urllib.error.URLError, socket.timeout) as e:
        logging.error("FastAPI connection error: %s", e)
        raise

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        history = body.get("conversationHistory", [])

        if not message:
            raise ValueError("message が空です")

        assistant_resp = call_fastapi(message)

        history.extend([
            {"role": "user",      "content": message},
            {"role": "assistant", "content": assistant_resp}
        ])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_resp,
                "conversationHistory": history
            })
        }

    except Exception as e:
        logging.exception("Error during processing")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({"success": False, "error": str(e)})
        }
