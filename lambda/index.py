# lambda/index.py
import json, os, urllib.request, urllib.error, socket, logging
from http import HTTPStatus               # 便利な定数


FASTAPI_BASE = os.environ.get("FASTAPI_URL", "https://0377-35-233-187-0.ngrok-free.app").rstrip("/")

# FastAPI 呼び出し関数
def call_fastapi(prompt: str, timeout: int = 45) -> str:
    """/generate へ JSON を POST し generated_text を返す"""
    payload = json.dumps({
        "prompt": prompt,
        "max_new_tokens": 512,
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9
    }).encode()

    req = urllib.request.Request(
        url=f"{FASTAPI_BASE}/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return body["generated_text"]          # ← FastAPI 側のキー名
    except urllib.error.HTTPError as e:
        # FastAPI が 4xx/5xx を返したとき
        logging.error("FastAPI HTTPError %s %s", e.code, e.reason)
        raise
    except (urllib.error.URLError, socket.timeout) as e:
        # ネットワーク到達不可 or タイムアウト
        logging.error("FastAPI network error: %s", e)
        raise

# Lambda ハンドラー
def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        history = body.get("conversationHistory", [])

        if not message:
            raise ValueError("message が空です")

        answer = call_fastapi(message)

        history += [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": answer}
        ]

        return {
            "statusCode": HTTPStatus.OK,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": answer,
                "conversationHistory": history
            })
        }

    except Exception as exc:
        logging.exception("Lambda error")
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({"success": False, "error": str(exc)})
        }

