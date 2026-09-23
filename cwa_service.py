import requests
import json
import urllib3

# 停用 SSL 警告 (部分 Windows 環境對 CWA 證書發出警告)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 中央氣象署 (CWA) API 設定
# ==========================================
# 請在此處填入您向 CWA 開放資料平台申請到的授權碼 (API Key)
API_KEY = "YOUR_API_KEY_HERE"

# CWA 一般天氣預報資料集 URL (F-C0032-001: 縣市預報)
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"


def fetch_weather_data(api_key: str = API_KEY, url: str = CWA_API_URL) -> dict:
    """
    發送 HTTP GET 請求向中央氣象署 API 取得預報 JSON 資料

    :param api_key: CWA 開放資料平台授權碼
    :param url: CWA API 請求網址
    :return: 成功回傳字典格式 (dict) 之 JSON 資料；失敗則回傳 None
    """
    # 設定請求 Header 與 Query 參數 (CWA API 支援放在 Authorization Header 或 Params)
    headers = {
        "Authorization": api_key
    }
    
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }

    print(f"[INFO] 正在向 {url} 發送 API 請求...")

    try:
        # 發送 GET 請求 (verify=False 可防止部分環境下 SSL 憑證驗證失敗)
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)

        # 檢查 HTTP 狀態碼 (200 代表成功)
        if response.status_code == 200:
            print("[SUCCESS] 成功存取中央氣象署 API！")
            data = response.json()
            return data
        else:
            print(f"[ERROR] 請求失敗，HTTP 狀態碼: {response.status_code}")
            print(f"[ERROR] 錯誤回應內容: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 發送請求時發生異常錯誤: {e}")
        return None


# 測試執行區塊
if __name__ == "__main__":
    print("=== 開始測試 fetch_weather_data() 函數 ===")
    weather_json = fetch_weather_data()
    
    if weather_json:
        print("\n=== 回傳 JSON 結構預覽 ===")
        print(json.dumps(weather_json, ensure_ascii=False, indent=2)[:500] + "\n...")
    else:
        print("\n[NOTE] 未取得資料 (可能因為 API_KEY 尚未填入無效或驗證未通過)。請填入有效的 API_KEY 後再試。")
