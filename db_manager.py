import sqlite3
import pandas as pd
import os

DB_NAME = "data.db"

def get_db_connection():
    """建立 SQLite 資料庫連線"""
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    """建立 TemperatureForecasts 資料表 (若不存在)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TemperatureForecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT NOT NULL,
            dataDate TEXT NOT NULL,
            mint REAL NOT NULL,
            maxt REAL NOT NULL,
            UNIQUE(regionName, dataDate) ON CONFLICT REPLACE
        )
    """)
    conn.commit()
    conn.close()

def save_forecasts(records):
    """將解析後的數據儲存至 SQLite 資料庫"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for r in records:
        cursor.execute("""
            INSERT OR REPLACE INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
            VALUES (?, ?, ?, ?)
        """, (r["regionName"], r["dataDate"], r["mint"], r["maxt"]))
        
    conn.commit()
    conn.close()

def query_forecasts(region_name=None):
    """從 SQLite 資料庫讀取氣象預報數據 (轉換為 Pandas DataFrame)"""
    init_db()
    conn = get_db_connection()
    
    if region_name and region_name != "全地區":
        query = "SELECT regionName, dataDate, mint, maxt FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate ASC"
        df = pd.read_sql_query(query, conn, params=(region_name,))
    else:
        query = "SELECT regionName, dataDate, mint, maxt FROM TemperatureForecasts ORDER BY dataDate ASC, regionName ASC"
        df = pd.read_sql_query(query, conn)
        
    conn.close()
    return df
