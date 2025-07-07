from linebot.models import (
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent
)

from config import ROOMMATES

def create_main_menu():
    """建立主選單"""
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="📅 查看本月排程", text="查看本月排程")),
        QuickReplyButton(action=MessageAction(label="👤 設定下個室友", text="設定下個室友")),
        QuickReplyButton(action=MessageAction(label="📝 更改本月排程", text="更改本月排程")),
    ]
    
    return QuickReply(items=quick_reply_buttons)

def create_roommate_selection():
    """建立室友選擇選單"""
    quick_reply_buttons = []
    for i, roommate in enumerate(ROOMMATES):
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