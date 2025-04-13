import os
import discord
from discord.ext import commands
from discord import Embed
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import pytz  # タイムゾーン対応のために追加

# .env ファイルから環境変数を読み込む
load_dotenv(dotenv_path='../.env')

# 環境変数の取得
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MTG_TIME = os.getenv('MTG_TIME', '12:00')  # デフォルト: 12:00に変更
REMINDER_MINUTES = int(os.getenv('REMINDER_MINUTES', '15'))  # デフォルト: 15分前
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tokyo')  # タイムゾーン設定（デフォルト：日本時間）

# タイムゾーンの設定
tz = pytz.timezone(TIMEZONE)

# MTG時間の解析
hour, minute = map(int, MTG_TIME.split(':'))

# Botのインテントを設定
intents = discord.Intents.default()
intents.message_content = True

# Botのインスタンス作成
bot = commands.Bot(command_prefix='!mtg-', intents=intents)

# スケジューラーの作成
scheduler = AsyncIOScheduler(timezone=tz)  # タイムゾーンを指定

# Botの準備完了時の処理
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    print(f'MTG time set to {MTG_TIME} every Sunday ({TIMEZONE})')
    print(f'Will send reminder {REMINDER_MINUTES} minutes before')
    
    # スケジューラーの設定
    setup_scheduler()
    
    # スケジューラーを開始
    scheduler.start()

def setup_scheduler():
    # チャンネルIDが正しいか確認
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    
    # MTG開始時のスケジュール (毎週日曜日)
    scheduler.add_job(
        send_mtg_start_notification,
        CronTrigger(day_of_week='sun', hour=hour, minute=minute, timezone=tz),
        args=[channel]
    )
    
    # リマインダー時間の計算
    now = datetime.now(tz)
    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    reminder_time = reminder_time - timedelta(minutes=REMINDER_MINUTES)
    reminder_hour = reminder_time.hour
    reminder_minute = reminder_time.minute
    
    # リマインダーのスケジュール (毎週日曜日)
    scheduler.add_job(
        send_mtg_reminder_notification,
        CronTrigger(day_of_week='sun', hour=reminder_hour, minute=reminder_minute, timezone=tz),
        args=[channel]
    )
    
    print(f"Scheduler set up. Next MTG: Every Sunday at {hour}:{minute:02d}")
    print(f"Reminder set for: Every Sunday at {reminder_hour}:{reminder_minute:02d}")

# MTG開始通知の送信
async def send_mtg_start_notification(channel):
    print(f"Sending MTG start notification to channel {channel.name}")
    embed = Embed(
        title="🎮 MTGが開始しました！",
        description="皆さん、参加してください。",
        color=0xFF0000
    )
    embed.timestamp = datetime.now(tz)
    
    await channel.send(embed=embed)

# MTGリマインダー通知の送信
async def send_mtg_reminder_notification(channel):
    print(f"Sending MTG reminder notification to channel {channel.name}")
    embed = Embed(
        title=f"⏰ MTG開始{REMINDER_MINUTES}分前です",
        description=f"{MTG_TIME}からMTGが始まります。準備をお願いします。",
        color=0xFFA500
    )
    embed.timestamp = datetime.now(tz)
    
    await channel.send(embed=embed)

# ヘルプコマンド - helpは予約語なのでinfo に変更
@bot.command(name='info')
async def info_command(ctx):
    embed = Embed(
        title="MTG通知Bot ヘルプ",
        description="MTGの開始時間を通知するBotです",
        color=0x0099FF
    )
    embed.add_field(name="!mtg-info", value="このヘルプメッセージを表示します", inline=False)
    embed.add_field(name="!mtg-next", value="次回のMTG時間を表示します", inline=False)
    embed.add_field(name="!mtg-set [時間]", value="MTGの時間を設定します (例: !mtg-set 15:30)", inline=False)
    embed.add_field(name="!mtg-status", value="現在の設定とボットの状態を表示します", inline=False)
    
    await ctx.reply(embed=embed)

# 次回MTGの情報表示コマンド
@bot.command(name='next')
async def next_command(ctx):
    now = datetime.now(tz)
    mtg_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 次の日曜日に設定
    current_day = now.weekday()  # 0は月曜、6は日曜
    if current_day == 6 and now < mtg_time:
        # 今日が日曜で、まだMTG時間前
        pass
    else:
        # 今日が日曜ではない、または今日が日曜だが既にMTG時間を過ぎている
        # 次の日曜まで日数を加算
        days_until_sunday = (6 - current_day) % 7
        mtg_time += timedelta(days=days_until_sunday)
    
    time_until_mtg = mtg_time - now
    days_until = time_until_mtg.days
    hours_until = time_until_mtg.seconds // 3600
    minutes_until = (time_until_mtg.seconds % 3600) // 60
    
    if days_until > 0:
        time_remaining_text = f"{days_until}日 {hours_until}時間 {minutes_until}分"
    else:
        time_remaining_text = f"{hours_until}時間 {minutes_until}分"
    
    embed = Embed(
        title="次回のMTG情報",
        description=f"次回のMTGは {mtg_time.strftime('%Y年%m月%d日')} の {MTG_TIME} からです (毎週日曜日)",
        color=0x0099FF
    )
    embed.add_field(name="残り時間", value=time_remaining_text)
    embed.timestamp = datetime.now(tz)
    
    await ctx.reply(embed=embed)

# ボットの状態確認コマンド（新規追加）
@bot.command(name='status')
async def status_command(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    channel_name = channel.name if channel else "見つかりません"
    
    embed = Embed(
        title="MTG通知Bot 状態",
        description="現在の設定と状態です",
        color=0x00FF00
    )
    embed.add_field(name="MTG時間", value=f"{MTG_TIME} (毎週日曜日)", inline=True)
    embed.add_field(name="リマインダー", value=f"MTG開始{REMINDER_MINUTES}分前", inline=True)
    embed.add_field(name="タイムゾーン", value=TIMEZONE, inline=True)
    embed.add_field(name="通知チャンネル", value=f"#{channel_name} (ID: {CHANNEL_ID})", inline=False)
    embed.timestamp = datetime.now(tz)
    
    await ctx.reply(embed=embed)

# MTG時間設定コマンド（管理者のみ）
@bot.command(name='set')
@commands.has_permissions(administrator=True)
async def set_command(ctx, new_time=None):
    global MTG_TIME, hour, minute
    
    if not new_time:
        await ctx.reply("正しい形式で入力してください。例: !mtg-set 15:30")
        return
    
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    if not time_pattern.match(new_time):
        await ctx.reply("時間形式が正しくありません。24時間形式で入力してください (例: 15:30)")
        return
    
    MTG_TIME = new_time
    hour, minute = map(int, MTG_TIME.split(':'))
    
    # スケジューラーを再設定
    scheduler.remove_all_jobs()
    setup_scheduler()
    
    await ctx.reply(f"MTG時間を {new_time} に設定しました。")


# 権限エラー処理
@set_command.error
async def set_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("この操作には管理者権限が必要です。")

# Botを実行
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("ログインに失敗しました。TOKENが正しいか確認してください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")