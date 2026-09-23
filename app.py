import streamlit as st
import sqlite3
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

from db_manager import init_db
from cwa_service import fetch_weather_data, parse_weather_data, save_weather_data

# ==========================================
# 台灣各縣市近似經緯度字典 (CITY_COORDS)
# ==========================================
CITY_COORDS = {
    "臺北市": [25.0375, 121.5637],
    "新北市": [24.9157, 121.6739],
    "基隆市": [25.1283, 121.7419],
    "桃園市": [24.9937, 121.3010],
    "新竹市": [24.8138, 120.9675],
    "新竹縣": [24.8387, 121.0177],
    "苗栗縣": [24.5602, 120.8214],
    "臺中市": [24.1477, 120.6736],
    "彰化縣": [24.0518, 120.5161],
    "南投縣": [23.9610, 120.9719],
    "雲林縣": [23.7093, 120.4313],
    "嘉義市": [23.4800, 120.4491],
    "嘉義縣": [23.4588, 120.5740],
    "臺南市": [22.9997, 120.2270],
    "高雄市": [22.6273, 120.3014],
    "屏東縣": [22.5519, 120.5487],
    "宜蘭縣": [24.7021, 121.7377],
    "花蓮縣": [23.9871, 121.6016],
    "臺東縣": [22.7613, 121.1444],
    "澎湖縣": [23.5711, 119.5793],
    "金門縣": [24.4493, 118.3766],
    "連江縣": [26.1505, 119.9499]
}

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
    
    # 若資料庫檔不存在或無資料，自動初始化並抓取
    if not os.path.exists(db_path):
        init_db()
        raw_json = fetch_weather_data()
        if raw_json:
            parsed = parse_weather_data(raw_json)
            save_weather_data(parsed)

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM TemperatureForecasts", conn)
        if not df.empty and 'regionName' in df.columns:
            # 去除地名首尾多餘空白
            df['regionName'] = df['regionName'].astype(str).str.strip()
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df


# 載入原始完整 DataFrame (df)
df = load_weather_data()

if df.empty:
    st.warning("⚠️ 目前資料庫無資料，請確認 API Key 或資料庫設定。")
else:
    # 1. 側邊欄 (st.sidebar) - 動態產生地區下拉選單 (過濾重複地點)
    st.sidebar.header("📍 選擇地區")
    unique_regions = sorted(df['regionName'].drop_duplicates().tolist())
    
    # 設定 key="selected_region_sb" 確保選單元件狀態穩定
    selected_region = st.sidebar.selectbox(
        "請選擇要觀看的地區 (regionName):",
        options=unique_regions,
        key="selected_region_sb"
    )

    # 2. 精準使用 selected_region 變數進行動態篩選
    filtered_df = df[df['regionName'] == selected_region].reset_index(drop=True)

    # 3. 主畫面動態標題與 Metrics 指標 (使用 f-string 動態綁定 selected_region)
    if not filtered_df.empty:
        current_data = filtered_df.iloc[0]

        # 完全動態標題 (使用 f-string)
        st.subheader(f"📌 {selected_region} 當前氣象指標")

        # 指標卡片 (st.metric)
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

        # 4. 詳細預報資料表格動態標題與表格 (完全動態綁定 selected_region)
        st.subheader(f"📋 {selected_region} 詳細資料表格")
        st.dataframe(
            filtered_df[['id', 'regionName', 'dataDate', 'minT', 'maxT', 'weather']],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

    # ==========================================
    # 地圖視覺化 (Steps 17, 18) — Folium 全台地圖與圖釘
    # ==========================================
    st.subheader("🗺️ 台灣全區互動式氣象地圖 (Folium Map)")

    # 當使用者選擇某縣市時，讓地圖自動移位焦點 (Step 18)
    if selected_region in CITY_COORDS:
        map_center = CITY_COORDS[selected_region]
        zoom_level = 10
    else:
        map_center = [23.7, 120.95]
        zoom_level = 7.5

    # 建立 Folium 地圖物件
    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")

    # 遍歷原始完整的 df (包含全台所有縣市圖釘)
    for _, row in df.iterrows():
        region_name = str(row.get('regionName', '')).strip()
        weather = row.get('weather', '未知')
        min_t = row.get('minT', 'N/A')
        max_t = row.get('maxT', 'N/A')

        if region_name in CITY_COORDS:
            coords = CITY_COORDS[region_name]

            # 依要求設定 Popup 格式
            popup_html = f"<b>{region_name}</b><br>天氣: {weather}<br>氣溫: {min_t}°C - {max_t}°C"
            
            # 側邊欄選中的地區使用紅色標籤提示，其餘為藍色
            icon_color = "red" if region_name == selected_region else "blue"

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{region_name}: {weather} ({min_t}°C ~ {max_t}°C)",
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(m)

    # 渲染 Folium 地圖 (使用 key=f"map_{selected_region}" 確保切換地區時地圖組件同步強制重繪)
    st_folium(
        m,
        width=900,
        height=500,
        returned_objects=[],
        key=f"map_{selected_region}"
    )

# 頁尾資訊
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Taiwan Weather Dashboard | CWA API × SQLite × Streamlit × Folium")
