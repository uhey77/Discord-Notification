import sys
import os
import datetime
import requests
import json
import time
from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv

# デバッグログを追加
print("スクリプト開始")

# 環境変数の読み込みを試みる
try:
    load_dotenv(dotenv_path='../.env')
    print("環境変数を.envから読み込みました")
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

# Kaggle認証情報を確認
KAGGLE_USERNAME = os.environ.get('KAGGLE_USERNAME')
KAGGLE_KEY = os.environ.get('KAGGLE_KEY')

print(f"Kaggle認証情報: ユーザー名が設定されているか: {bool(KAGGLE_USERNAME)}, APIキーが設定されているか: {bool(KAGGLE_KEY)}")

def send_discord_notification(message):
    payload = {'content': message}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # エラーがあれば例外を発生
        print(f"Discord通知送信成功: {message}")
        return response
    except Exception as e:
        print(f"Discord通知送信失敗: {e}")
        return None

def main():
    send_discord_notification('Submission status check start')
    
    # Kaggle API認証情報を確認
    try:
        # 認証を試みる前にkaggle.jsonファイルの存在を確認
        home = os.path.expanduser("~")
        kaggle_dir = os.path.join(home, ".kaggle")
        kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
        
        if os.path.exists(kaggle_json):
            print(f"kaggle.jsonファイルが存在します: {kaggle_json}")
            with open(kaggle_json, 'r') as f:
                credentials = json.load(f)
                print(f"kaggle.jsonの内容: ユーザー名あり={bool(credentials.get('username'))}, キーあり={bool(credentials.get('key'))}")
        else:
            print(f"kaggle.jsonファイルが見つかりません。新規作成します。")
            os.makedirs(kaggle_dir, exist_ok=True)
            with open(kaggle_json, 'w') as f:
                json.dump({"username": KAGGLE_USERNAME, "key": KAGGLE_KEY}, f)
            os.chmod(kaggle_json, 0o600)  # パーミッション設定
            print(f"kaggle.jsonファイルを作成しました: {kaggle_json}")
        
        # 認証と競技情報の取得を試みる
        api = KaggleApi()
        print("KaggleAPIインスタンスを作成しました")
        
        # 認証を試みる
        api.authenticate()
        print("Kaggle認証に成功しました")

        # コンペティション情報の取得を試みる
        try:
            COMPETITION = 'drawing-with-llms'  # 必要に応じて変更
            print(f"コンペティション '{COMPETITION}' の情報を取得します")
            
            # 先に利用可能なコンペティションのリストを取得してデバッグする
            competitions = api.competitions_list()
            competition_names = [comp.ref for comp in competitions]
            print(f"利用可能なコンペティション: {competition_names}")
            
            if COMPETITION not in competition_names:
                message = f"エラー: コンペティション '{COMPETITION}' が見つかりません。利用可能なコンペティションを確認してください。"
                print(message)
                send_discord_notification(message)
                return
            
            # サブミッションの取得を試みる
            submissions = api.competition_submissions(COMPETITION)
            print(f"サブミッション取得成功: {len(submissions)} 件")
            
            # 以下、元のコードのまま
            submission_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

            if not submissions:
                print("No submissions found.")
                send_discord_notification("No submissions found.")
                return

            if submission_index >= len(submissions):
                print("Invalid submission index.")
                send_discord_notification("Invalid submission index.")
                return

            latest_submission = submissions[submission_index]
            status = latest_submission.status  # 例: SubmissionStatus.COMPLETE

            elapsed_time = calc_elapsed_minutes(latest_submission.date)

            # "COMPLETE" が含まれていれば完了とみなす
            if "COMPLETE" in str(status).upper():
                message = (
                    f"[Completed] Submission is still {status}. "
                    f"Elapsed time: {elapsed_time} min.\n"
                    f"notebook_url: https://kaggle.com{latest_submission.url}"
                )
            else:
                message = (
                    f"[IN PROGRESS] Submission is still {status}. "
                    f"Elapsed time: {elapsed_time} min.\n"
                    f"notebook_url: https://kaggle.com{latest_submission.url}"
                )

            send_discord_notification(message)
            
        except Exception as e:
            error_message = f"コンペティション情報の取得中にエラーが発生しました: {str(e)}"
            print(error_message)
            send_discord_notification(error_message)
            
    except Exception as e:
        error_message = f"Kaggle認証中にエラーが発生しました: {str(e)}"
        print(error_message)
        send_discord_notification(error_message)
        
def calc_elapsed_minutes(submit_time):
    now = datetime.datetime.utcnow()  # Kaggle submission time はUTC
    return int((now - submit_time).total_seconds() / 60)

if __name__ == '__main__':
    main()