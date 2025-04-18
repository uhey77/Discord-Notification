import sys
from kaggle.api.kaggle_api_extended import KaggleApi
import datetime
import requests
import os
from dotenv import load_dotenv

# .envファイルを読み込む試行（失敗しても続行）
try:
    load_dotenv(dotenv_path='../.env')
except:
    pass


# GitHubアクションの環境変数を優先
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
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(message)
    return response


def main():
    send_discord_notification('Submission status check start')

    api = KaggleApi()
    api.authenticate()

    # コマンドライン引数がある場合はその番号を取得。なければ 0。
    submission_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    COMPETITION = 'drawing-with-llms'  # 必要に応じて変更
    submissions = api.competition_submissions(COMPETITION)

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


def calc_elapsed_minutes(submit_time):
    now = datetime.datetime.utcnow()  # Kaggle submission time はUTC
    return int((now - submit_time).total_seconds() / 60)


if __name__ == '__main__':
    main()
