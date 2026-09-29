import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import altair as alt
import datetime
from db_manager import init_db
from cwa_service import fetch_weather_data, parse_weather_data

# 台灣各縣市近似經緯度字典
CITY_COORDS = {
    "臺北市": [25.0375, 121.5637], "新北市": [24.9157, 121.6739], "基隆市": [25.1283, 121.7419],
    "桃園市": [24.9937, 121.3010], "新竹市": [24.8138, 120.9675], "新竹縣": [24.8387, 121.0177],
    "苗栗縣": [24.5602, 120.8214], "臺中市": [24.1477, 120.6736], "彰化縣": [24.0518, 120.5161],
    "南投縣": [23.9610, 120.9719], "雲林縣": [23.7093, 120.4313], "嘉義市": [23.4800, 120.4491],
    "嘉義縣": [23.4588, 120.5740], "臺南市": [22.9997, 120.2270], "高雄市": [22.6273, 120.3014],
    "屏東縣": [22.5519, 120.5487], "宜蘭縣": [24.7021, 121.7377], "花蓮縣": [23.9871, 121.6016],
    "臺東縣": [22.7613, 121.1444], "澎湖縣": [23.5711, 119.5793], "金門縣": [24.4493, 118.3766],
    "連江縣": [26.1505, 119.9499]
}

st.set_page_config(page_title="Taiwan Weather Dashboard", page_icon="⛅", layout="wide")

# 鎖定防翻譯與字體設定
st.markdown("""
    <style>body { font-family: "Microsoft JhengHei", sans-serif; }</style>
    <meta name="google" content="notranslate">
""", unsafe_allow_html=True)

st.title('Taiwan Weather Dashboard')
st.markdown("---")

def safe_save_to_db(data_list):
    if not data_list: return
    conn = sqlite3.connect("data.db")
    df = pd.DataFrame(data_list)
    conn.execute("DELETE FROM TemperatureForecasts")
    df.to_sql("TemperatureForecasts", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

# 實時更新機制：快取存活時間設定為 3 小時 (10800秒)
@st.cache_data(ttl=10800)
def load_weather_data() -> pd.DataFrame:
    init_db() # 確保雲端資料庫存在
    raw_json = fetch_weather_data()
    if raw_json:
        parsed = parse_weather_data(raw_json)
        safe_save_to_db(parsed)
        print(f"[{datetime.datetime.now()}] 已在雲端自動更新 {len(parsed)} 筆最新氣象資料！")

    conn = sqlite3.connect("data.db")
    try:
        df = pd.read_sql_query("SELECT * FROM TemperatureForecasts", conn)
        if not df.empty and 'regionName' in df.columns:
            df['regionName'] = df['regionName'].astype(str).str.strip()
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

df = load_weather_data()

if df.empty:
    st.warning("⚠️ 目前資料庫無資料，請確認 API Key 是否設定正確。")
else:
    st.sidebar.header("📍 選擇地區")
    unique_regions = sorted(df['regionName'].drop_duplicates().tolist())
    selected_region = st.sidebar.selectbox("請選擇要觀看的地區:", options=unique_regions)

    filtered_df = df[df['regionName'] == selected_region].reset_index(drop=True)

    if not filtered_df.empty:
        current_data = filtered_df.iloc[0]

        st.subheader(f"📌 {selected_region} 當前氣象指標")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌤️ 天氣狀況", str(current_data.get('weather', '未知')))
        with col2:
            st.metric("🔥 實際溫度", f"{current_data.get('maxT')} °C")
        with col3:
            st.metric("❄️ 體感溫度", f"{current_data.get('minT')} °C")
        
        st.markdown("---")

        # 這裡就是您最期待的 3 小時氣溫折線圖！
        st.subheader(f"📈 {selected_region} 未來氣溫趨勢圖 (每3小時)")
        chart_data = filtered_df[['dataDate', 'maxT', 'minT']].copy()
        chart_data = chart_data.rename(columns={'maxT': '實際溫度', 'minT': '體感溫度', 'dataDate': '日期與時間'})
        chart_data = chart_data.melt(id_vars=['日期與時間'], value_vars=['實際溫度', '體感溫度'], var_name='溫度類型', value_name='溫度 (°C)')
        
        line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
            x=alt.X('日期與時間:N', title='日期與時間', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('溫度 (°C):Q', title='溫度 (°C)', scale=alt.Scale(zero=False)),
            color=alt.Color('溫度類型:N', scale=alt.Scale(domain=['實際溫度', '體感溫度'], range=['#ff4b4b', '#0068c9'])),
            tooltip=['日期與時間', '溫度類型', '溫度 (°C)']
        ).properties(height=400)
        
        st.altair_chart(line_chart, use_container_width=True)
        st.markdown("---")

    st.subheader("🗺️ 台灣全區互動式氣象地圖")

    map_center = CITY_COORDS.get(selected_region, [23.7, 120.95])
    zoom_level = 10 if selected_region in CITY_COORDS else 7.5

    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")
    latest_df = df.drop_duplicates(subset=['regionName'], keep='first')

    for _, row in latest_df.iterrows():
        region_name = str(row.get('regionName', '')).strip()
        weather = row.get('weather', '未知')
        min_t, max_t = row.get('minT', 'N/A'), row.get('maxT', 'N/A')

        if region_name in CITY_COORDS:
            coords = CITY_COORDS[region_name]
            popup_html = f"<b>{region_name}</b><br>天氣: {weather}<br>實際: {max_t}°C<br>體感: {min_t}°C"
            icon_color = "red" if region_name == selected_region else "blue"

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{region_name}: {weather}",
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(m)

    st_folium(m, width=900, height=500, returned_objects=[], key=f"map_{selected_region}")
