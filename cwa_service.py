import requests
import json
from datetime import datetime, timedelta

# CWA API 預設開放資料 API Key (可改為使用者自訂 KEY)
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

def get_mock_weather_data():
    """
    提供備用預設範例資料，確保在無 API Key 時網站依然可完整呈現互動功能。
    """
    today = datetime.now()
    regions = ["北部地區", "中部地區", "南部地區", "東部地區", "東北部地區", "東南部地區"]
    mock_records = []

    base_temps = {
        "北部地區": (18, 26),
        "中部地區": (20, 30),
        "南部地區": (22, 31),
        "東部地區": (21, 28),
        "東北部地區": (19, 25),
        "東南部地區": (22, 29)
    }

    for region in regions:
        min_base, max_base = base_temps[region]
        for i in range(7):
            date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            # 模擬微幅氣溫起伏
            mint = min_base + (i % 3) - 1
            maxt = max_base + (i % 2)
            mock_records.append({
                "regionName": region,
                "dataDate": date_str,
                "mint": float(mint),
                "maxt": float(maxt)
            })
    return mock_records


def fetch_cwa_weather_data(api_key=None):
    """
    從中央氣象署 CWA API 抓取並解析氣象 JSON 資料
    """
    if not api_key or api_key.strip() == "":
        return get_mock_weather_data()

    params = {
        "Authorization": api_key,
        "format": "JSON"
    }

    try:
        response = requests.get(CWA_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return parse_cwa_json(data)
        else:
            print(f"API Error {response.status_code}, falling back to demo data.")
            return get_mock_weather_data()
    except Exception as e:
        print(f"Fetch failed: {e}, using demo data.")
        return get_mock_weather_data()


def parse_cwa_json(data):
    """
    解析 CWA API JSON 結構，提取地區名稱與 MinT/MaxT
    """
    records = []
    try:
        location_list = data.get("records", {}).get("location", [])
        for loc in location_list:
            location_name = loc.get("locationName", "")
            
            # 地區對照
            region_map = {
                "臺北市": "北部地區", "新北市": "北部地區", "基隆市": "北部地區", "桃園市": "北部地區",
                "臺中市": "中部地區", "彰化縣": "中部地區", "南投縣": "中部地區", "雲林縣": "中部地區",
                "高雄市": "南部地區", "臺南市": "南部地區", "屏東縣": "南部地區",
                "花蓮縣": "東部地區", "宜蘭縣": "東北部地區", "臺東縣": "東南部地區"
            }
            region_name = region_map.get(location_name, "北部地區")

            elements = loc.get("weatherElement", [])
            mint_dict = {}
            maxt_dict = {}

            for elem in elements:
                elem_name = elem.get("elementName")
                if elem_name == "MinT":
                    for time_slot in elem.get("time", []):
                        start_time = time_slot.get("startTime", "").split(" ")[0]
                        val = float(time_slot.get("parameter", {}).get("parameterName", 20))
                        mint_dict[start_time] = val
                elif elem_name == "MaxT":
                    for time_slot in elem.get("time", []):
                        start_time = time_slot.get("startTime", "").split(" ")[0]
                        val = float(time_slot.get("parameter", {}).get("parameterName", 28))
                        maxt_dict[start_time] = val

            all_dates = set(mint_dict.keys()).union(set(maxt_dict.keys()))
            for d in sorted(all_dates):
                if d:
                    records.append({
                        "regionName": region_name,
                        "dataDate": d,
                        "mint": mint_dict.get(d, 20.0),
                        "maxt": maxt_dict.get(d, 28.0)
                    })

        return records if records else get_mock_weather_data()
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return get_mock_weather_data()
