import calendar
from datetime import date, timedelta
import json
import os

roommates = ['室友A', '室友B', '室友C']
CONFIG_FILE = 'roommate_config.json'

def load_config():
    """載入設定檔，如果不存在則建立預設設定"""
    default_config = {
        'next_roommate_index': 0,  # 下一個輪到的室友索引
        'last_updated_month': None,  # 最後更新的月份
        'last_updated_year': None   # 最後更新的年份
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 確保所有必要的鍵都存在
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
    """取得一個月的週次，根據新規則過濾"""
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    all_weeks = []
    
    for week in c.monthdatescalendar(year, month):
        # 檢查這週是否應該包含在本月
        week_start = week[0]
        week_end = week[-1]
        
        # 如果週的開始日期在上個月，則跳過（第一週規則）
        if week_start.month < month or (week_start.month == 12 and month == 1):
            continue
            
        # 如果這週有任何一天在這個月，就納入（包含跨到下個月的最後一週）
        if any(day.month == month for day in week):
            all_weeks.append(week)
    
    return all_weeks

def generate_schedule(year, month, show_debug=False):
    """產生排程並更新下一個輪到的室友"""
    config = load_config()
    weeks = get_weeks_of_month(year, month)
    
    if not weeks:
        return "本月沒有符合條件的週次"
    
    msg_blocks = []
    current_roommate_index = config['next_roommate_index']
    
    if show_debug:
        print(f"Debug: {year}年{month}月 - 共{len(weeks)}週")
        print(f"Debug: 本月第一週從 {roommates[current_roommate_index]} 開始 (索引: {current_roommate_index})")
    
    for i, week in enumerate(weeks):
        start_day = week[0]
        end_day = week[-1]
        roommate_index = (current_roommate_index + i) % len(roommates)
        roommate = roommates[roommate_index]
        
        msg = (
            f"倒垃圾 - {roommate}\n"
            f"時間：{start_day.strftime('%Y/%m/%d')} 00:00 ~ {end_day.strftime('%Y/%m/%d')} 23:59"
        )
        msg_blocks.append(msg)
        
        if show_debug:
            print(f"Debug: 第{i+1}週 ({start_day.strftime('%m/%d')}-{end_day.strftime('%m/%d')}) -> {roommate}")
    
    # 更新下一個月的起始室友索引
    next_roommate_index = (current_roommate_index + len(weeks)) % len(roommates)
    config['next_roommate_index'] = next_roommate_index
    config['last_updated_year'] = year
    config['last_updated_month'] = month
    save_config(config)
    
    if show_debug:
        print(f"Debug: 下個月將從 {roommates[next_roommate_index]} 開始 (索引: {next_roommate_index})")
    
    return "\n\n".join(msg_blocks)

def reset_schedule():
    """重置排程，從室友A開始"""
    config = {
        'next_roommate_index': 0,
        'last_updated_month': None,
        'last_updated_year': None
    }
    save_config(config)
    print("排程已重置，下次將從室友A開始")

def show_current_status():
    """顯示目前的狀態"""
    config = load_config()
    next_roommate = roommates[config['next_roommate_index']]
    
    print(f"目前狀態：")
    print(f"下一個輪到的室友：{next_roommate}")
    
    if config['last_updated_year'] and config['last_updated_month']:
        print(f"最後更新：{config['last_updated_year']}年{config['last_updated_month']}月")
    else:
        print("尚未產生過排程")

def manually_set_next_roommate():
    """手動設定下一個輪到的室友"""
    print("室友列表：")
    for i, roommate in enumerate(roommates):
        print(f"{i+1}. {roommate}")
    
    try:
        choice = int(input("請選擇下一個輪到的室友編號: ")) - 1
        if 0 <= choice < len(roommates):
            config = load_config()
            config['next_roommate_index'] = choice
            save_config(config)
            print(f"已設定下一個輪到的室友為：{roommates[choice]}")
        else:
            print("無效的選擇")
    except ValueError:
        print("請輸入有效的數字")

def show_continuous_schedule(start_year, start_month, num_months=3):
    """顯示連續幾個月的排程，用來驗證順序是否正確"""
    print("=== 連續月份排程驗證 ===")
    current_year, current_month = start_year, start_month
    
    # 備份當前設定
    original_config = load_config().copy()
    
    for i in range(num_months):
        print(f"\n--- {current_year}年{current_month}月 ---")
        schedule = generate_schedule(current_year, current_month, show_debug=True)
        print(schedule)
        
        # 移到下個月
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    # 詢問是否要保留這些更改
    choice = input("\n是否要保留這些排程更改？(y/N): ").lower()
    if choice != 'y':
        save_config(original_config)
        print("已還原到原始狀態")

def show_week_analysis(year, month):
    """分析某個月的週次分配"""
    print(f"\n=== {year}年{month}月週次分析 ===")
    
    # 顯示原始的所有週次
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    all_weeks_original = list(c.monthdatescalendar(year, month))
    
    print("原始所有週次：")
    for i, week in enumerate(all_weeks_original, 1):
        start_day = week[0]
        end_day = week[-1]
        print(f"週{i}: {start_day.strftime('%Y/%m/%d')} ~ {end_day.strftime('%Y/%m/%d')}")
    
    # 顯示過濾後的週次
    filtered_weeks = get_weeks_of_month(year, month)
    print(f"\n過濾後的週次（共{len(filtered_weeks)}週）：")
    for i, week in enumerate(filtered_weeks, 1):
        start_day = week[0]
        end_day = week[-1]
        print(f"週{i}: {start_day.strftime('%Y/%m/%d')} ~ {end_day.strftime('%Y/%m/%d')}")

if __name__ == "__main__":
    print("室友輪值排程系統（改進版）")
    print("室友順序:", roommates)
    print("規則：")
    print("- 第一週如包含上個月日期則不顯示於本月")
    print("- 最後一週如包含下個月日期則顯示於本月")
    print("- 自動記錄下一個輪到的室友\n")
    
    while True:
        try:
            print("\n請選擇功能：")
            print("1. 查看單月排程")
            print("2. 查看連續月份排程驗證")
            print("3. 查看目前狀態")
            print("4. 手動設定下一個輪到的室友")
            print("5. 重置排程")
            print("6. 週次分析")
            print("7. 退出")
            
            choice = input("請輸入選項 (1-7): ")
            
            if choice == '1':
                month = int(input("請輸入月份 (1-12): "))
                year = int(input("請輸入年份 (預設2025): ") or "2025")
                if 1 <= month <= 12:
                    print(f"\n{year}年{month}月排程：")
                    print(generate_schedule(year, month))
                else:
                    print("請輸入有效的月份 (1-12)")
            
            elif choice == '2':
                start_month = int(input("請輸入起始月份 (1-12): "))
                start_year = int(input("請輸入起始年份 (預設2025): ") or "2025")
                num_months = int(input("請輸入要顯示的月份數量 (預設3): ") or "3")
                show_continuous_schedule(start_year, start_month, num_months)
            
            elif choice == '3':
                show_current_status()
            
            elif choice == '4':
                manually_set_next_roommate()
            
            elif choice == '5':
                confirm = input("確定要重置排程嗎？(y/N): ")
                if confirm.lower() == 'y':
                    reset_schedule()
            
            elif choice == '6':
                month = int(input("請輸入要分析的月份 (1-12): "))
                year = int(input("請輸入年份 (預設2025): ") or "2025")
                if 1 <= month <= 12:
                    show_week_analysis(year, month)
                else:
                    print("請輸入有效的月份 (1-12)")
            
            elif choice == '7':
                print("再見！")
                break
            
            else:
                print("請輸入有效選項")
                
        except ValueError:
            print("請輸入有效的數字")
        except KeyboardInterrupt:
            print("\n再見！")
            break