from datetime import date
import os

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
)

from core.ui import create_main_menu, create_roommate_selection, create_schedule_flex_message
from core.utils import generate_schedule, set_next_roommate_index
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, ROOMMATES


app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    
    try:
        # 主要功能判斷
        if text in ["倒垃圾咪狗"]:
            reply_text = "🏠 室友輪值排程系統\n\n請選擇功能："
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text, quick_reply=create_main_menu())
            )
            
        elif text == "查看本月排程":
            today = date.today()
            schedules, config = generate_schedule(today.year, today.month)
            
            if isinstance(schedules, str):  # 錯誤訊息
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=schedules, quick_reply=create_main_menu())
                )
            else:
                next_roommate = ROOMMATES[config['next_roommate_index']]
                flex_msg = create_schedule_flex_message(schedules, today.year, today.month)
                status_msg = TextSendMessage(
                    text=f"✅ 排程已更新！\n下個月將從 {next_roommate} 開始",
                    quick_reply=create_main_menu()
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    [flex_msg, status_msg]
                )
            
        elif text == "設定下個室友":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇下一個輪到的室友：", quick_reply=create_roommate_selection())
            )
            
        elif text.startswith("選擇室友"):
            roommate_index = int(text.replace("選擇室友", ""))
            set_next_roommate_index(roommate_index)
            
            selected_roommate = ROOMMATES[roommate_index]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"✅ 已設定下一個輪到的室友為：{selected_roommate}",
                    quick_reply=create_main_menu()
                )
            )

        else:
            pass
            
    except Exception as e:
        pass

if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))