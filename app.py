import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from cwa_service import fetch_cwa_weather_data
from db_manager import init_db, save_forecasts, query_forecasts

# Streamlit 頁面設定
st.set_page_config(
    page_title="Taiwan Weather Forecast | 煥哥 AI 微課程",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS 樣式
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 頁面標題
st.markdown('<p class="main-title">⛅ 台灣天氣預報動態儀表板 (Taiwan Weather Forecast)</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">從氣象資料到互動式天氣預報應用 | CWA API × Python × SQLite × Streamlit × Folium</p>', unsafe_allow_html=True)

# 側邊欄：設定與資料更新
st.sidebar.header("⚙️ 控制面板 (Control Panel)")

cwa_api_key = st.sidebar.text_input("輸入 CWA Open Data API Key:", type="password", help="留空將自動載入模擬展示資料")

if st.sidebar.button("🔄 更新/擷取最新氣象資料"):
    with st.spinner("正在向中央氣象署 CWA 請求最新資料中..."):
        records = fetch_cwa_weather_data(cwa_api_key)
        save_forecasts(records)
        st.sidebar.success(f"成功更新 {len(records)} 筆資料至 SQLite (data.db)！")

# 確保資料庫已初始化並有基礎數據
init_db()
df_all = query_forecasts()
if df_all.empty:
    records = fetch_cwa_weather_data()
    save_forecasts(records)
    df_all = query_forecasts()

# 選擇地區與檢視選項
regions = ["全地區", "北部地區", "中部地區", "南部地區", "東部地區", "東北部地區", "東南部地區"]
selected_region = st.sidebar.selectbox("🗺️ 選擇預報地區 (Select Region):", regions)

st.sidebar.markdown("---")
st.sidebar.markdown("**👨‍🏫 導師資訊**: 煥哥 (Huan Ge)")
st.sidebar.markdown("**🛠️ 開發工具**: Antigravity IDE × Gemini")

# 主要內容分頁
tab1, tab2, tab3 = st.tabs(["📊 折線圖與數據表", "🗺️ 台灣地圖視覺化", "📝 專案與 SQLite 資訊"])

with tab1:
    st.subheader(f"📈 {selected_region} — 一週最高溫與最低溫趨勢圖")
    df_filtered = query_forecasts(selected_region)

    if not df_filtered.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            # 準備折線圖數據
            chart_df = df_filtered.pivot(index="dataDate", columns="regionName", values=["mint", "maxt"]) if selected_region == "全地區" else df_filtered.set_index("dataDate")[["mint", "maxt"]]
            
            if selected_region != "全地區":
                chart_df.columns = ["最低氣溫 (MinT)", "最高氣溫 (MaxT)"]
                st.line_chart(chart_df, color=["#0000FF", "#FF0000"])
            else:
                st.line_chart(df_filtered.pivot(index="dataDate", columns="regionName", values="maxt"))

        with col2:
            st.subheader("📋 氣象預報資料表")
            display_df = df_filtered.rename(columns={
                "regionName": "地區",
                "dataDate": "日期",
                "mint": "最低溫 (°C)",
                "maxt": "最高溫 (°C)"
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🗺️ 互動式台灣氣溫地圖 (Folium Map)")
    
    # 選擇日期
    dates = sorted(df_all["dataDate"].unique())
    selected_date = st.selectbox("📅 選擇觀測日期:", dates if dates else ["2026-04-14"])

    # 建立 Folium 地圖 (中心點設於台灣)
    m = folium.Map(location=[23.7, 121.0], zoom_start=7, tiles="CartoDB positron")

    region_coords = {
        "北部地區": (25.04, 121.51),
        "中部地區": (24.14, 120.67),
        "南部地區": (22.62, 120.30),
        "東部地區": (23.98, 121.60),
        "東北部地區": (24.75, 121.75),
        "東南部地區": (22.75, 121.15)
    }

    df_date = df_all[df_all["dataDate"] == selected_date]

    for _, row in df_date.iterrows():
        reg = row["regionName"]
        mint = row["mint"]
        maxt = row["maxt"]
        if reg in region_coords:
            lat, lon = region_coords[reg]
            avg_temp = (mint + maxt) / 2
            
            color = "blue" if avg_temp < 22 else "orange" if avg_temp < 28 else "red"
            
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{reg}</b><br>日期: {selected_date}<br>最低溫: {mint}°C<br>最高溫: {maxt}°C",
                tooltip=f"{reg}: {mint}°C ~ {maxt}°C",
                icon=folium.Icon(color=color, icon="cloud")
            ).add_to(m)

    st_folium(m, width=900, height=500)

with tab3:
    st.subheader("💾 SQLite 資料庫結構與學習架構 (Database & Architecture)")
    
    st.markdown("""
    **SQL 查詢驗證範例:**
    ```sql
    SELECT DISTINCT regionName FROM TemperatureForecasts;
    SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';
    ```
    """)
    
    st.subheader("⚡ Vibe Coding 開發流程與工具")
    st.markdown("""
    - **IDE**: Antigravity IDE
    - **LLM**: Gemini 2.0
    - **Version Control**: GitHub (`https://github.com/a9110118888/AIOT-L3_hw.git`)
    - **Data Pipeline**: CWA API -> Requests -> JSON ETL -> Pandas -> SQLite3 -> Streamlit + Folium
    """)

st.markdown("---")
st.caption("© 2026 煥哥 AI 創新微課程 Taiwan Weather Forecast Dashboard | All Rights Reserved.")
