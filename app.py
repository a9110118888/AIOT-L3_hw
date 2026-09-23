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

    # 2. 根據使用者選擇的地區篩選 DataFrame (用於指標與下方表格)
    filtered_df = df[df['regionName'] == selected_region].reset_index(drop=True)

    if not filtered_df.empty:
        # 取得最新一筆天氣預報數據
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

    # ==========================================
    # 地圖視覺化 (Steps 17, 18) — Folium 全台地圖與圖釘
    # ==========================================
    st.subheader("🗺️ 台灣全區互動式氣象地圖 (Folium Map)")

    # 4. (進階互動 - Step 18): 依據選擇的地區設定地圖中心點與縮放層級
    if selected_region in CITY_COORDS:
        map_center = CITY_COORDS[selected_region]
        zoom_level = 10
    else:
        map_center = [23.7, 120.95]
        zoom_level = 7.5

    # 建立 Folium 地圖物件
    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")

    # 5. 正確的圖釘與 Popup: 使用 for 迴圈遍歷完整的 DataFrame (包含所有縣市，不受側邊欄篩選影響)
    for _, row in df.iterrows():
        region_name = row.get('regionName')
        weather = row.get('weather', '未知')
        min_t = row.get('minT', 'N/A')
        max_t = row.get('maxT', 'N/A')

        # 從經緯度字典中抓出對應座標
        if region_name in CITY_COORDS:
            coords = CITY_COORDS[region_name]

            # 依要求設定 Popup 格式: "<b>{地區名稱}</b><br>天氣: {天氣}<br>氣溫: {最低溫}°C - {最高溫}°C"
            popup_html = f"<b>{region_name}</b><br>天氣: {weather}<br>氣溫: {min_t}°C - {max_t}°C"
            
            # 側邊欄選中的地區使用紅色標籤提示，其餘為藍色
            icon_color = "red" if region_name == selected_region else "blue"

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{region_name}: {weather} ({min_t}°C ~ {max_t}°C)",
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(m)

    # 在 Streamlit 中渲染 Folium 地圖
    st_folium(m, width=900, height=500)

    st.markdown("---")

    # 6. 主畫面下方顯示詳細預報資料表格 (st.dataframe)
    st.subheader(f"📋 {selected_region} 詳細預報資料表格")
    st.dataframe(
        filtered_df[['id', 'regionName', 'dataDate', 'minT', 'maxT', 'weather']],
        use_container_width=True,
        hide_index=True
    )

# 頁尾資訊
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Taiwan Weather Dashboard | CWA API × SQLite × Streamlit × Folium")
