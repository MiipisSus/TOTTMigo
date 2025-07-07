import calendar
from .db import load_config, save_config, load_schedules, save_schedules
from config import ROOMMATES


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
    """產生排程（只在第一次產生該月時才寫入，否則直接讀取）"""
    schedules_all = load_schedules()
    key = f"{year}-{month}"
    config = load_config()

    # 若該月已存在，直接回傳
    if key in schedules_all:
        return schedules_all[key]['schedules'], config

    weeks = get_weeks_of_month(year, month)
    if not weeks:
        return "本月沒有符合條件的週次", config

    schedules = []
    current_roommate_index = config['next_roommate_index']
    for i, week in enumerate(weeks):
        start_day = week[0]
        end_day = week[-1]
        roommate_index = (current_roommate_index + i) % len(ROOMMATES)
        roommate = ROOMMATES[roommate_index]
        schedule_info = {
            'roommate': roommate,
            'start_date': start_day.strftime('%Y/%m/%d'),
            'end_date': end_day.strftime('%Y/%m/%d'),
            'week_num': i + 1
        }
        schedules.append(schedule_info)

    # 更新下一個月的起始室友索引
    next_roommate_index = (current_roommate_index + len(weeks)) % len(ROOMMATES)
    config['next_roommate_index'] = next_roommate_index
    config['last_updated_year'] = year
    config['last_updated_month'] = month
    save_config(config)

    # 寫入該月排程
    schedules_all[key] = {
        'schedules': schedules
    }
    save_schedules(schedules_all)
    return schedules, config

def set_next_roommate_index(roommate_index):
    """設定下一個輪到的室友"""
    config = load_config()
    if 0 <= roommate_index < len(ROOMMATES):
        config['next_roommate_index'] = roommate_index
        save_config(config)
        return ROOMMATES[roommate_index]
    else:
        raise ValueError("無效的室友索引")