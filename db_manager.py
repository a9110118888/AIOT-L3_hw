import sqlite3
import os
from typing import List, Dict, Any

# 資料庫名稱
DB_NAME = "data.db"


def get_connection():
    """取得 SQLite 資料庫連線"""
    return sqlite3.connect(DB_NAME)


def init_db():
    """
    初始化 SQLite 資料庫與建立 TemperatureForecasts 資料表
    
    資料表欄位:
    - id (INTEGER PRIMARY KEY AUTOINCREMENT)
    - regionName (TEXT)
    - dataDate (TEXT)
    - minT (REAL)
    - maxT (REAL)
    - weather (TEXT)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TemperatureForecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT,
            dataDate TEXT,
            minT REAL,
            maxT REAL,
            weather TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[INFO] 資料庫 {DB_NAME} 與資料表 TemperatureForecasts 初始化完成。")


def save_weather_data(data_list: List[Dict[str, Any]]):
    """
    將整理好的氣象資料清單寫入 SQLite 資料庫
    
    :param data_list: 解析後的 List[Dict] 天氣資料
    """
    if not data_list:
        print("[WARNING] 沒有任何氣象資料可寫入資料庫。")
        return

    # 確保資料庫與資料表已初始化
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 清空舊資料，保持永遠只保留最新預報
        cursor.execute("DELETE FROM TemperatureForecasts")
        print("[INFO] 已清空舊的預報資料 (DELETE FROM TemperatureForecasts)。")

        # 批次寫入新資料
        insert_query = """
            INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT, weather)
            VALUES (?, ?, ?, ?, ?)
        """
        
        insert_records = []
        for item in data_list:
            region_name = item.get("regionName")
            data_date = item.get("dataDate")
            min_t = item.get("minT")
            max_t = item.get("maxT")
            weather = item.get("weather") or item.get("wx")
            insert_records.append((region_name, data_date, min_t, max_t, weather))

        cursor.executemany(insert_query, insert_records)
        conn.commit()
        print(f"[SUCCESS] 成功寫入 {len(insert_records)} 筆氣象預報資料至資料庫！")

    except sqlite3.Error as e:
        print(f"[ERROR] 寫入資料庫時發生錯誤: {e}")
        conn.rollback()

    finally:
        conn.close()


# 測試程式碼
if __name__ == "__main__":
    print("=== 測試 db_manager.py 初始化 ===")
    init_db()
