# lambda/index.py
import json
import os
import urllib.request
import logging


FASTAPI_URL = "https://0b49-35-233-187-0.ngrok-free.app"


def call_fastapi(message: str, timeout: int = 30) -> str:
    if not FASTAPI_URL:
        raise RuntimeError("FASTAPI_URL が設定されていません")

    req = urllib.request.Request(
        url=f"{FASTAPI_URL}",                         # エンドポイント
        data=json.dumps({"message": message}).encode(),    # JSON ボディ
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
        return data.get("response", "")


# Lambda ハンドラー
def lambda_handler(event, context):
    try:
        logging.info("Received event: %s", json.dumps(event))

        # ----------- リクエスト解析 -----------
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        conversation_history = body.get("conversationHistory", [])

        if not message:
            raise ValueError("message が空です")

        # ----------- FastAPI 呼び出し -----------
        assistant_response = call_fastapi(message)

        # ----------- 会話履歴更新 -----------
        conversation_history.extend([
            {"role": "user",      "content": message},
            {"role": "assistant", "content": assistant_response}
        ])

        # ----------- 正常レスポンス -----------
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
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as e:
        logging.exception("Error during processing")

        # ----------- エラー応答 -----------
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
