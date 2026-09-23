import streamlit as st
import sqlite3
import pandas as pd
import os

from db_manager import init_db
from cwa_service import fetch_weather_data, parse_weather_data
from db_manager import save_weather_data

# 設定 Streamlit 網頁標題與 Layout
st.set_page_config(
    page_title="Taiwan Weather Dashboard",
    page_icon="⛅",
    layout="wide"
)

# 網頁大標題 (Step 11)
st.title('Taiwan Weather Dashboard')
st.markdown("---")


# 從 SQLite 資料庫讀取資料 (Step 12)
def load_weather_data() -> pd.DataFrame:
    """連接 data.db 並讀取 TemperatureForecasts 資料表為 DataFrame"""
    db_path = "data.db"
    
    # 若資料庫檔不存在或資料表為空，自動先初始化並抓取資料
    if not os.path.exists(db_path):
        init_db()
        raw_json = fetch_weather_data()
        if raw_json:
            parsed = parse_weather_data(raw_json)
            save_weather_data(parsed)

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM TemperatureForecasts", conn)
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df


# 載入資料
df = load_weather_data()

if df.empty:
    st.warning("⚠️ 目前資料庫無資料，請確認 API Key 或資料庫設定。")
else:
    # 建立互動元件與版面 (Steps 13-16)

    # 1. 側邊欄 (st.sidebar) - 動態產生地區下拉選單 (過濾重複地點)
    st.sidebar.header("📍 選擇地區")
    unique_regions = df['regionName'].drop_duplicates().tolist()
    
    selected_region = st.sidebar.selectbox(
        "請選擇要觀看的地區 (regionName):",
        options=unique_regions
    )

    # 2. 根據使用者選擇的地區篩選 DataFrame
    filtered_df = df[df['regionName'] == selected_region].reset_index(drop=True)

    if not filtered_df.empty:
        # 取得最新第一筆天氣預報數據
        current_data = filtered_df.iloc[0]

        st.subheader(f"📌 {selected_region} 當前氣象指標")

        # 3. 主畫面顯示地區當前 weather、maxT、minT (使用 st.metric)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="🌤️ 天氣狀況 (weather)",
                value=str(current_data.get('weather', '未知'))
            )

        with col2:
            st.metric(
                label="🔥 最高氣溫 (maxT)",
                value=f"{current_data.get('maxT')} °C"
            )

        with col3:
            st.metric(
                label="❄️ 最低氣溫 (minT)",
                value=f"{current_data.get('minT')} °C"
            )

        st.markdown("---")

        # 4. 主畫面下方顯示詳細預報資料表格 (st.dataframe)
        st.subheader(f"📋 {selected_region} 詳細預報資料表格")
        st.dataframe(
            filtered_df[['id', 'regionName', 'dataDate', 'minT', 'maxT', 'weather']],
            use_container_width=True,
            hide_index=True
        )

# 頁尾資訊
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Taiwan Weather Dashboard | CWA API × SQLite × Streamlit")
