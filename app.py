import json
import websocket
import threading
import time
import sys
from intents import INTENTS
from dotenv import load_dotenv
import os
import requests

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")

bot_user_id = None
heartbeat_interval = None
sequence = None


def on_message(ws, message):
    global sequence, heartbeat_interval,bot_user_id
    payload = json.loads(message)
    op = payload.get("op")
    t = payload.get("t")
    d = payload.get("d")

    if op == 10:
        print("Hello received. Starting heartbeat and identifying...")
        heartbeat_interval = d["heartbeat_interval"] / 1000

        def heartbeat():
            while True:
                if not ws or not ws.sock or not ws.sock.connected:
                    break
                time.sleep(heartbeat_interval)
                ws.send(json.dumps({"op": 1, "d": sequence}))

        threading.Thread(target=heartbeat, daemon=True).start()

        ws.send(
            json.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": BOT_TOKEN,
                        "intents": intents_value,
                        "properties": {
                            "$os": "linux",
                            "$browser": "disco",
                            "$device": "disco",
                        },
                    },
                }
            )
        )

    if op == 0:
        sequence = payload["s"]

        if t == "READY":
            bot_user_id = d["user"]["id"]
            print(f"🤖 BotのユーザーID : {bot_user_id}")

        elif t == "MESSAGE_CREATE":
            channel_id = d["channel_id"]
            content = d.get("content", "")
            author = d["author"]
            message_id = d["id"]
            if d["author"]["id"] == bot_user_id:
                return 
            display_name = author.get("global_name") if "global_name" in author else author["username"]
            if channel_id == "1339597202774950070": #お絵描きのチャンネルID
                attachments = d.get("attachments", [])
                has_image = any(
                    att.get("content_type", "").startswith("image")
                    for att in attachments
                )

                if has_image:

                    thread_url = (
                        f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/threads"
                    )
                    headers = {
                        "Authorization": f"Bot {BOT_TOKEN}",
                        "Content-Type": "application/json",
                    }
                    thread_payload = {
                        "name": f"{display_name}のすばらしい絵！",
                        "auto_archive_duration": 60,
                        "type": 11,
                    }
                    response = requests.post(
                        thread_url, headers=headers, json=thread_payload
                    )
                    if response.status_code == 201:
                        thread_data = response.json()
                        print(f"🧵 スレッド作成: {thread_data['name']}")
                    else:
                        print(
                            f"❌ スレッド作成失敗: {response.status_code} {response.text}"
                        )
                else:
                    delete_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{d['id']}"
                    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
                    response = requests.delete(delete_url, headers=headers)
                    if response.status_code == 204:
                        print(f"🗑️ メッセージ削除: {content}")
                    else:
                        print(
                            f"❌ メッセージ削除失敗: {response.status_code} {response.text}"
                        )


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Connection closed")


def on_open(ws):
    print("Connected to Discord Gateway")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        SELECTED_INTENTS = INTENTS
    else:
        SELECTED_INTENTS = sys.argv[1:]

    with open("intents.json", "r", encoding="utf-8") as f:
        intents_data = json.load(f)
    INTENTS_MAP = {k: v["value"] for k, v in intents_data["intents"].items()}

    intents_value = 0
    for intent_name in SELECTED_INTENTS:
        value = INTENTS_MAP.get(intent_name)
        if value is None:
            print(f"Warning: Unknown intent '{intent_name}' ignored.")
        else:
            intents_value |= value

    print("Selected intents:", SELECTED_INTENTS)

    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://gateway.discord.gg/?v=10&encoding=json",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
            )
            ws.run_forever()
            time.sleep(5)
        except KeyboardInterrupt:
            print("END THIS APP")
            break