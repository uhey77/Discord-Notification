import sys
import os
import datetime
import requests
from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv

# 環境変数の読み込みを試みる
try:
    load_dotenv(dotenv_path='../.env')
except Exception as e:
    print(f".envファイルの読み込みに失敗しました: {e}")

# GitHubアクションの環境変数を確認
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URLが設定されていません。")

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKENが設定されていません。")

DISCORD_CHANNEL_ID = os.environ.get('DISCORD_CHANNEL_ID')
if not DISCORD_CHANNEL_ID:
    raise ValueError("DISCORD_CHANNEL_IDが設定されていません。")

def send_discord_notification(message):
    payload = {'content': message}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(message)
        return response
    except Exception as e:
        print(f"Discord通知送信失敗: {e}")
        return None

def main():
    send_discord_notification('Submission status check start')

    # 現在の日時
    now = datetime.datetime.utcnow()
    formatted_date = now.strftime("%Y年%m月%d日 %H:%M:%S UTC")
    
    # 固定メッセージ
    message = (
        f"🔄 Kaggle Submission Status Check ({formatted_date})\n\n"
        f"Kaggle APIでの自動チェックは現在利用できません。\n"
        f"以下のリンクから最新のサブミッション状況を確認してください：\n"
        f"📊 https://www.kaggle.com/competitions/drawing-with-llms/submissions"
    )
    
    send_discord_notification(message)

if __name__ == '__main__':
    main()