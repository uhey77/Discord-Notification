import sys
from kaggle.api.kaggle_api_extended import KaggleApi
import datetime
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URLが設定されていません。")
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKENが設定されていません。")
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
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



# import sys
# from kaggle.api.kaggle_api_extended import KaggleApi
# import datetime
# import time
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# WEBHOOK_URL = os.getenv('WEBHOOK_URL')
# if not WEBHOOK_URL:
#     raise ValueError("WEBHOOK_URLが設定されていません。 .envファイルを確認してください。")
# DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
# if not DISCORD_BOT_TOKEN:
#     raise ValueError("DISCORD_BOT_TOKENが設定されていません。 .envファイルを確認してください。")
# DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
# if not DISCORD_CHANNEL_ID:
#     raise ValueError("DISCORD_CHANNEL_IDが設定されていません。 .envファイルを確認してください。")

# def send_discord_notification(message):
#     payload = {'content': message}
#     headers = {'Content-Type': 'application/json'}
#     response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
#     print(message)
#     return response

# def main():
#     # 最初に任意の通知を送る（不要なら削除可）
#     send_discord_notification('Submission status check start')

#     api = KaggleApi()
#     api.authenticate()

#     # コマンドライン引数がある場合はその番号、なければ 0 番目の submission を対象とする
#     submission_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

#     # 使用するコンペ名を設定
#     COMPETITION = 'drawing-with-llms'  # 必要に応じて変更
#     submissions = api.competition_submissions(COMPETITION)

#     # submissionが存在するかチェック
#     if not submissions:
#         print("No submissions found.")
#         send_discord_notification("No submissions found.")
#         return

#     if submission_index >= len(submissions):
#         print("Invalid submission index.")
#         send_discord_notification("Invalid submission index.")
#         return

#     latest_submission = submissions[submission_index]
#     status = latest_submission.status

#     # Submissionが完了(complete)しているかどうかを1回チェック
#     if status == 'complete':
#         elapsed_time = calc_elapsed_minutes(latest_submission.date)
#         message = (
#             f"[COMPLETE] run-time: {elapsed_time} min, "
#             f"LB: {latest_submission.publicScore}, "
#             f"file_name: {latest_submission.file_name}, "
#             f"description: {latest_submission.description}\n"
#             f"notebook_url: https://kaggle.com{latest_submission.url}"
#         )
#         send_discord_notification(message)
#     else:
#         elapsed_time = calc_elapsed_minutes(latest_submission.date)
#         message = (
#             f"[IN PROGRESS] Submission is still {status}. "
#             f"Elapsed time: {elapsed_time} min.\n"
#             f"notebook_url: https://kaggle.com{latest_submission.url}"
#         )
#         send_discord_notification(message)

# def calc_elapsed_minutes(submit_time):
#     """Submissionが開始してからの経過分数を返す。"""
#     now = datetime.datetime.utcnow()  # KaggleのdateがUTC基準
#     return int((now - submit_time).total_seconds() / 60)

# if __name__ == '__main__':
#     main()
