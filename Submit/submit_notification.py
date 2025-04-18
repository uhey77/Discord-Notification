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

# コンペティション名を環境変数から取得するか、デフォルト値を使用
COMPETITION_NAME = os.environ.get('COMPETITION_NAME', 'drawing-with-llms')

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

    try:
        api = KaggleApi()
        api.authenticate()
        
        # 利用可能なコンペティションを取得
        competitions = api.competitions_list()
        competition_names = [comp.ref for comp in competitions]
        
        # 最初に、指定されたコンペティション名が利用可能かチェック
        if COMPETITION_NAME not in competition_names:
            # コンペティションが見つからない場合、利用可能なコンペティションを表示
            available_comps = ', '.join(competition_names[:5]) + (', ...' if len(competition_names) > 5 else '')
            message = (
                f"コンペティション '{COMPETITION_NAME}' が見つかりません。\n"
                f"利用可能なコンペティション例: {available_comps}\n"
                f"正しいコンペティション名を環境変数 COMPETITION_NAME に設定してください。"
            )
            send_discord_notification(message)
            return
            
        # コマンドライン引数がある場合はその番号を取得。なければ 0。
        submission_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

        # サブミッションを取得
        submissions = api.competition_submissions(COMPETITION_NAME)
        
        if not submissions:
            send_discord_notification(f"コンペティション '{COMPETITION_NAME}' にサブミッションが見つかりません。")
            return

        if submission_index >= len(submissions):
            send_discord_notification(f"無効なサブミッションインデックス: {submission_index}, 最大値: {len(submissions)-1}")
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
        error_message = f"エラーが発生しました: {str(e)}"
        send_discord_notification(error_message)

def calc_elapsed_minutes(submit_time):
    now = datetime.datetime.utcnow()  # Kaggle submission time はUTC
    return int((now - submit_time).total_seconds() / 60)

if __name__ == '__main__':
    main()