import requests
import json
import urllib3
from typing import List, Dict, Any, Optional

# 停用 SSL 警告 (部分 Windows 環境對 CWA 憑證跳出警告)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 中央氣象署 (CWA) API 設定
# ==========================================
# 請在此處填入您向 CWA 開放資料平台申請到的授權碼 (API Key)
API_KEY = "CWA-173529DD-AAEE-4B6B-89E0-1112D4AAD41F"

# CWA 一般天氣預報資料集 URL (F-C0032-001: 縣市預報)
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"


def fetch_weather_data(api_key: str = API_KEY, url: str = CWA_API_URL) -> Optional[dict]:
    """
    發送 HTTP GET 請求向中央氣象署 API 取得預報 JSON 資料

    :param api_key: CWA 開放資料平台授權碼
    :param url: CWA API 請求網址
    :return: 成功回傳字典格式 (dict) 之 JSON 資料；失敗則回傳 None
    """
    headers = {
        "Authorization": api_key
    }
    
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }

    print(f"[INFO] 正在向 {url} 發送 API 請求...")

    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)

        if response.status_code == 200:
            print("[SUCCESS] 成功存取中央氣象署 API！")
            return response.json()
        else:
            print(f"[ERROR] 請求失敗，HTTP 狀態碼: {response.status_code}")
            print(f"[ERROR] 錯誤回應內容: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 發送請求時發生異常錯誤: {e}")
        return None


def parse_weather_data(json_data: Optional[dict]) -> List[Dict[str, Any]]:
    """
    解析 CWA API (F-C0032-001) 回傳的 JSON 結構，提取關鍵天氣資訊
    
    轉換為 List[Dict] 結構，範例:
    [
        {"regionName": "臺北市", "dataDate": "2026-09-23 18:00:00", "minT": 25, "maxT": 30, "wx": "多雲短暫陣雨"},
        ...
    ]

    :param json_data: fetch_weather_data 回傳之原生 JSON 字典
    :return: 解析後的 List[Dict] 天氣資料清單
    """
    parsed_list: List[Dict[str, Any]] = []

    if not json_data or "records" not in json_data or "location" not in json_data["records"]:
        print("[WARNING] JSON 資料格式無效或未包含 location 紀錄。")
        return parsed_list

    location_list = json_data["records"]["location"]

    for loc in location_list:
        location_name = loc.get("locationName", "未知地點")
        min_t = None
        max_t = None
        wx = None
        data_date = None

        weather_elements = loc.get("weatherElement", [])
        for elem in weather_elements:
            elem_name = elem.get("elementName")
            time_slots = elem.get("time", [])

            if time_slots:
                # 提取第一筆時間區段
                first_slot = time_slots[0]
                
                # 若尚未設定 dataDate，使用第一筆時間區段的 startTime
                if not data_date:
                    data_date = first_slot.get("startTime")

                param_name = first_slot.get("parameter", {}).get("parameterName")

                # 解析最低溫
                if elem_name == "MinT":
                    try:
                        min_t = int(param_name)
                    except (ValueError, TypeError):
                        min_t = param_name
                
                # 解析最高溫
                elif elem_name == "MaxT":
                    try:
                        max_t = int(param_name)
                    except (ValueError, TypeError):
                        max_t = param_name

                # (可選) 解析天氣現象描述
                elif elem_name == "Wx":
                    wx = param_name

        # 組合成地點 Dictionary
        item = {
            "regionName": location_name,
            "dataDate": data_date,
            "minT": min_t,
            "maxT": max_t,
            "wx": wx
        }
        parsed_list.append(item)

    return parsed_list


# 測試執行區塊
if __name__ == "__main__":
    print("=== 開始測試 CWA API 請求與資料解析 ===")
    
    # 1. 發送 GET 請求取得原生 JSON
    raw_json = fetch_weather_data()
    
    if raw_json:
        # 2. 解析 JSON 資料結構
        parsed_data = parse_weather_data(raw_json)
        
        print(f"\n[SUCCESS] 成功解析 {len(parsed_data)} 個縣市的天氣預報資料！\n")
        print("=== 解析後的資料結構 (前 5 筆地點範例 List[Dict]) ===")
        print(json.dumps(parsed_data[:5], ensure_ascii=False, indent=2))
        
        print("\n=== 所有地點快速檢視 ===")
        for item in parsed_data:
            print(f"[地點] {item['regionName']} | [時間] {item['dataDate']} | [氣溫] {item['minT']}°C ~ {item['maxT']}°C | [天況] {item['wx']}")
    else:
        print("\n[NOTE] 無法取得資料，請檢查 API Key 是否正確。")
