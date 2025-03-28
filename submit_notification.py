import sys
from kaggle.api.kaggle_api_extended import KaggleApi
import datetime
import time
import requests
import os
from dotenv import load_dotenv
from tqdm import tqdm
try:
    from tqdm._utils import _format_meter as format_meter
except ImportError:
        def fallback_format_meter(n, total, elapsed, prefix='', ascii=True):
            bar_length = 20
            progress = int((n / total) * bar_length)
            bar = '[' + '=' * progress + ' ' * (bar_length - progress) + ']'
            percentage = (n / total) * 100

            def sec_to_time(s):
                m, s = divmod(int(s), 60)
                h, m = divmod(m, 60)
                return f"{h:d}:{m:02d}:{s:02d}"

            elapsed_str = sec_to_time(elapsed)
            remaining = (elapsed / n * (total - n)) if n > 0 else 0
            remaining_str = sec_to_time(remaining)
            return f"{percentage:.0f}%| {n}/{total} {bar} [{elapsed_str}<{remaining_str}]"
        format_meter = fallback_format_meter


load_dotenv()

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URLが設定されていません。 .envファイルを確認してください。")
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKENが設定されていません。 .envファイルを確認してください。")
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
if not DISCORD_CHANNEL_ID:
    raise ValueError("DISCORD_CHANNEL_IDが設定されていません。 .envファイルを確認してください。")


def send_discord_notification(message):
    webhook_url = WEBHOOK_URL
    payload = {'content': message}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, json=payload, headers=headers)
    print(message)
    return response


def post_discord_progress_message(message):
    # メッセージIDを返してもらうには "?wait=true" が必要
    url = f"{WEBHOOK_URL}?wait=true"
    payload = {'content': message}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:  # 200 で JSON が返ってくる
        data = response.json()
        return data.get("id")
    else:
        print("Failed to post progress message:", response.status_code, response.text)
        return None


def update_discord_progress_message(message, notebook_url, message_id):
    # メッセージを編集するエンドポイントにも "?wait=true" を付ける
    update_url = f"{WEBHOOK_URL}/messages/{message_id}?wait=true"
    headers = {'Content-Type': 'application/json'}

    # # --- 埋め込みを利用してクリック可能なリンクを設定 ---
    # payload = {
    #     "content": message,  # テキストとして進捗情報を残す
    #     "embeds": [
    #         {
    #             "title": "Notebook Link",
    #             "url": f"https://kaggle.com{notebook_url}",  # クリックで飛べるURL
    #             "description": "Click the title above to open the notebook!"
    #         }
    #     ]
    # }

    # Embedの代わりにテキストとしてリンクを付ける
    text_with_link = f"{message}\nNotebook Link (text only): https://kaggle.com{notebook_url}"

    payload = {
        "content": text_with_link
    }

    response = requests.patch(update_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to update message:", response.status_code, response.text)
        return None


def main():
    send_discord_notification('submit check start')
    progress_message = "Progress: 0/540 min"
    progress_message_id = post_discord_progress_message(progress_message)

    api = KaggleApi()
    api.authenticate()

    # コマンドライン引数がある場合はその番号、なければ 0 番目の submission を対象とする
    submission_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    submissions = api.competition_submissions(COMPETITION)

    # submissionが存在するかチェック
    if not submissions:
        print("No submissions found.")
        sys.exit()

    if submission_index >= len(submissions):
        print("Invalid submission index.")
        sys.exit()

    latest_submission = submissions[submission_index]
    latest_ref = str(latest_submission.ref)
    submit_time = latest_submission.date
    pbar = tqdm(total=540)
    start_t = time.time()  # 開始時刻を記録

    while True:
        # 最新の submission 一覧を取得して、対象の submission を探す
        submissions = api.competition_submissions(COMPETITION)
        current_submission = next((sub for sub in submissions if str(sub.ref) == latest_ref), None)
        if current_submission is None:
            print("Submission not found.")
            pbar.close()
            sys.exit(1)

        status = current_submission.status
        now = datetime.datetime.utcnow()  # submit_timeがUTCであることを前提
        elapsed_time = int((now - submit_time).total_seconds() / 60) + 1

        if status == 'complete':
            message = (
                f'run-time: {elapsed_time} min, LB: {current_submission.publicScore}, '
                # f'file_name: {current_submission.file_name}, description: {current_submission.description}\n'
                # f'{current_submission.url}'
                f'file_name: {current_submission.file_name}, description: {current_submission.description}\n'
                f'notebook_url: {current_submission.url}'
            )
            print('\r' + message)
            send_discord_notification(message)
            sys.exit(0)
        else:
            progress = min(int(elapsed_time / 540 * 20), 20)

            pbar.n = elapsed_time
            pbar.refresh()  # 内部状態を更新
            progress_str = format_meter(
                n=pbar.n,
                total=pbar.total,
                elapsed=(time.time() - start_t),
                prefix='',
                ascii=True
            )

            # notebookのURLを追記
            progress_str = f"{progress_str}\nnotebook_url: kaggle.com{current_submission.url}"

            update_discord_progress_message(progress_str, current_submission.url, progress_message_id)
            print('\r' + progress_str, end='')
            time.sleep(60)


if __name__ == '__main__':
    COMPETITION = 'drawing-with-llms'  # コンペ名を設定
    main()
