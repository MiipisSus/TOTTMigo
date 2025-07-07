import json
import os


CONFIG_FILE = 'roommate_config.json'
SCHEDULES_FILE = 'roommate_schedules.json'

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

def load_schedules():
    """載入所有月份的排程"""
    if os.path.exists(SCHEDULES_FILE):
        try:
            with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告：無法載入排程檔: {e}")
    return {}

def save_schedules(schedules):
    """儲存所有月份的排程"""
    try:
        with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：無法儲存排程檔: {e}")