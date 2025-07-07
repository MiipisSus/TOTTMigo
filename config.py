from dotenv import load_dotenv
import os

load_dotenv()

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
# 室友設定
ROOMMATES = os.getenv('ROOMMATES', '').split(',')