from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction,
    PostbackEvent
)
import calendar
from datetime import date, timedelta
import json
import os
import re

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 室友設定
roommates = ['思妤', '怡彣', '小豆']
CONFIG_FILE = 'roommate_config.json'

# 用戶狀態管理
user_states = {}

def load_config():
    """載入設定檔"""
    default_config = {
        'next_roommate_index': 0,
        'last_updated_month': None,
        'last_updated_year': None
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except:
            pass
    
    return default_config

def save_config(config):
    """儲存設定檔"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：無法儲存設定檔: {e}")

def get_weeks_of_month(year, month):
    """取得一個月的週次，根據規則過濾"""
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    all_weeks = []
    
    for week in c.monthdatescalendar(year, month):
        week_start = week[0]
        week_end = week[-1]
        
        # 如果週的開始日期在上個月，則跳過
        if week_start.month < month or (week_start.month == 12 and month == 1):
            continue
            
        # 如果這週有任何一天在這個月，就納入
        if any(day.month == month for day in week):
            all_weeks.append(week)
    
    return all_weeks

def generate_schedule(year, month):
    """產生排程"""
    config = load_config()
    weeks = get_weeks_of_month(year, month)
    
    if not weeks:
        return "本月沒有符合條件的週次", config
    
    schedules = []
    current_roommate_index = config['next_roommate_index']
    
    for i, week in enumerate(weeks):
        start_day = week[0]
        end_day = week[-1]
        roommate_index = (current_roommate_index + i) % len(roommates)
        roommate = roommates[roommate_index]
        
        schedule_info = {
            'roommate': roommate,
            'start_date': start_day.strftime('%Y/%m/%d'),
            'end_date': end_day.strftime('%Y/%m/%d'),
            'week_num': i + 1
        }
        schedules.append(schedule_info)
    
    # 更新下一個月的起始室友索引
    next_roommate_index = (current_roommate_index + len(weeks)) % len(roommates)
    config['next_roommate_index'] = next_roommate_index
    config['last_updated_year'] = year
    config['last_updated_month'] = month
    save_config(config)
    
    return schedules, config

def create_main_menu():
    """建立主選單"""
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="📅 查看本月排程", text="查看本月排程")),
        QuickReplyButton(action=MessageAction(label="📝 查看指定月份", text="指定月份")),
        QuickReplyButton(action=MessageAction(label="ℹ️ 查看狀態", text="查看狀態")),
        QuickReplyButton(action=MessageAction(label="⚙️ 設定", text="設定選單"))
    ]
    
    return QuickReply(items=quick_reply_buttons)

def create_settings_menu():
    """建立設定選單"""
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="👤 設定下個室友", text="設定下個室友")),
        QuickReplyButton(action=MessageAction(label="🔄 重置排程", text="重置排程")),
        QuickReplyButton(action=MessageAction(label="📊 週次分析", text="週次分析")),
        QuickReplyButton(action=MessageAction(label="🏠 回主選單", text="主選單"))
    ]
    
    return QuickReply(items=quick_reply_buttons)

def create_roommate_selection():
    """建立室友選擇選單"""
    quick_reply_buttons = []
    for i, roommate in enumerate(roommates):
        quick_reply_buttons.append(
            QuickReplyButton(action=MessageAction(label=roommate, text=f"選擇室友{i}"))
        )
    quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(label="❌ 取消", text="主選單"))
    )
    
    return QuickReply(items=quick_reply_buttons)

def create_schedule_flex_message(schedules, year, month):
    """建立排程的 Flex Message"""
    contents = []
    
    # 標題
    contents.append(
        TextComponent(
            text=f"{year}年{month}月 倒垃圾排程",
            weight="bold",
            size="lg",
            color="#1DB446"
        )
    )
    
    # 分隔線
    contents.append(
        TextComponent(text=" ", size="sm")
    )
    
    # 排程內容
    for schedule in schedules:
        contents.append(
            TextComponent(
                text=f"第{schedule['week_num']}週：{schedule['roommate']}",
                weight="bold",
                color="#333333"
            )
        )
        contents.append(
            TextComponent(
                text=f"{schedule['start_date']} ~ {schedule['end_date']}",
                size="sm",
                color="#666666"
            )
        )
        contents.append(
            TextComponent(text=" ", size="xs")
        )
    
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=contents
        )
    )
    
    return FlexSendMessage(alt_text=f"{year}年{month}月排程", contents=bubble)

def analyze_weeks(year, month):
    """分析週次"""
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    all_weeks_original = list(c.monthdatescalendar(year, month))
    filtered_weeks = get_weeks_of_month(year, month)
    
    analysis = f"📊 {year}年{month}月週次分析\n\n"
    analysis += f"原始週次數：{len(all_weeks_original)}\n"
    analysis += f"過濾後週次數：{len(filtered_weeks)}\n\n"
    
    analysis += "📋 採用的週次：\n"
    for i, week in enumerate(filtered_weeks, 1):
        start_day = week[0]
        end_day = week[-1]
        analysis += f"第{i}週：{start_day.strftime('%m/%d')} ~ {end_day.strftime('%m/%d')}\n"
    
    return analysis

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
    user_id = event.source.user_id
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
                next_roommate = roommates[config['next_roommate_index']]
                flex_msg = create_schedule_flex_message(schedules, today.year, today.month)
                status_msg = TextSendMessage(
                    text=f"✅ 排程已更新！\n下個月將從 {next_roommate} 開始",
                    quick_reply=create_main_menu()
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    [flex_msg, status_msg]
                )
            
        elif text == "指定月份":
            user_states[user_id] = {'action': 'waiting_for_month'}
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入月份（例如：7 或 2025/7）")
            )
            
        elif text == "查看狀態":
            config = load_config()
            next_roommate = roommates[config['next_roommate_index']]
            
            status_text = f"📋 目前狀態\n\n"
            status_text += f"下一個輪到：{next_roommate}\n"
            
            if config['last_updated_year'] and config['last_updated_month']:
                status_text += f"最後更新：{config['last_updated_year']}年{config['last_updated_month']}月"
            else:
                status_text += "尚未產生過排程"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=status_text, quick_reply=create_main_menu())
            )
            
        elif text == "設定選單":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚙️ 設定選單", quick_reply=create_settings_menu())
            )
            
        elif text == "設定下個室友":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇下一個輪到的室友：", quick_reply=create_roommate_selection())
            )
            
        elif text.startswith("選擇室友"):
            roommate_index = int(text.replace("選擇室友", ""))
            config = load_config()
            config['next_roommate_index'] = roommate_index
            save_config(config)
            
            selected_roommate = roommates[roommate_index]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"✅ 已設定下一個輪到的室友為：{selected_roommate}",
                    quick_reply=create_main_menu()
                )
            )
            
        elif text == "重置排程":
            user_states[user_id] = {'action': 'confirm_reset'}
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"⚠️ 確定要重置排程嗎？這會將排程重新從{roommates[0]}開始。\n\n回覆「確定」來確認，或「取消」來取消。")
            )
            
        elif text == "週次分析":
            user_states[user_id] = {'action': 'waiting_for_analysis_month'}
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入要分析的月份（例如：7 或 2025/7）")
            )
            
        # 處理用戶狀態相關的輸入
        elif user_id in user_states:
            handle_user_state(event, user_id, text)

        else:
            pass
            
    except Exception as e:
        pass

def handle_user_state(event, user_id, text):
    """處理用戶狀態相關的輸入"""
    state = user_states[user_id]
    
    if state['action'] == 'waiting_for_month':
        # 解析月份輸入
        year, month = parse_month_input(text)
        if year and month:
            schedules, config = generate_schedule(year, month)
            
            if isinstance(schedules, str):  # 錯誤訊息
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=schedules, quick_reply=create_main_menu())
                )
            else:
                next_roommate = roommates[config['next_roommate_index']]
                flex_msg = create_schedule_flex_message(schedules, year, month)
                status_msg = TextSendMessage(
                    text=f"✅ 排程已更新！\n下個月將從 {next_roommate} 開始",
                    quick_reply=create_main_menu()
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    [flex_msg, status_msg]
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 請輸入正確的月份格式（例如：7 或 2025/7）")
            )
        del user_states[user_id]
        
    elif state['action'] == 'waiting_for_analysis_month':
        year, month = parse_month_input(text)
        if year and month:
            analysis = analyze_weeks(year, month)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=analysis, quick_reply=create_main_menu())
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 請輸入正確的月份格式（例如：7 或 2025/7）")
            )
        del user_states[user_id]
        
    elif state['action'] == 'confirm_reset':
        if text == "確定":
            config = {
                'next_roommate_index': 0,
                'last_updated_month': None,
                'last_updated_year': None
            }
            save_config(config)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅ 排程已重置，下次將從室友A開始", quick_reply=create_main_menu())
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 重置已取消", quick_reply=create_main_menu())
            )
        del user_states[user_id]

def parse_month_input(text):
    """解析月份輸入"""
    try:
        if '/' in text:
            parts = text.split('/')
            if len(parts) == 2:
                year = int(parts[0])
                month = int(parts[1])
            else:
                return None, None
        else:
            month = int(text)
            year = date.today().year
        
        if 1 <= month <= 12 and 2020 <= year <= 2030:
            return year, month
        else:
            return None, None
    except ValueError:
        return None, None

if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))