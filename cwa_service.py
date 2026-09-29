import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ⚠️ 貼上後，請務必把這裡換成您的真實 API Key！
API_KEY = "CWA-BB7B3F46-4892-4D32-9E5B-EC9D28B0D42F" 
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089"

def fetch_weather_data():
    url = f"{CWA_API_URL}?Authorization={API_KEY}&format=JSON"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API 請求失敗: {e}")
        return None

def parse_weather_data(json_data):
    parsed_data = []
    try:
        locations = json_data.get('records', {}).get('Locations', [{}])[0].get('Location', [])
        
        for loc in locations:
            region_name = loc.get('LocationName', loc.get('locationName', '未知'))
            weather_elements = loc.get('WeatherElement', loc.get('weatherElement', []))
            
            elements = {}
            for e in weather_elements:
                ename = e.get('ElementName', e.get('elementName'))
                if ename: elements[ename] = e
            
            # --- 關鍵修正：改用中文尋找氣象元素！ ---
            t_elem = elements.get('溫度', {})
            at_elem = elements.get('體感溫度', {})
            wx_elem = elements.get('天氣現象', {})
            # ----------------------------------------
            
            t_times = t_elem.get('Time', t_elem.get('time', []))
            at_times = at_elem.get('Time', at_elem.get('time', []))
            wx_times = wx_elem.get('Time', wx_elem.get('time', []))
            
            if not t_times: continue
            
            # 這裡設定抓取未來 16 個時段 (共 48 小時)
            num_records = min(16, len(t_times))
            for i in range(num_records):
                start_time = t_times[i].get('DataTime', t_times[i].get('StartTime', t_times[i].get('dataTime', t_times[i].get('startTime', ''))))
                
                try:
                    t_val_arr = t_times[i].get('ElementValue', t_times[i].get('elementValue', [{}]))
                    t_val = float(t_val_arr[0].get('Temperature', t_val_arr[0].get('value', t_val_arr[0].get('溫度', 0))))
                except: t_val = 0.0
                
                try:
                    if at_times:
                        at_val_arr = at_times[i].get('ElementValue', at_times[i].get('elementValue', [{}]))
                        at_val = float(at_val_arr[0].get('ApparentTemperature', at_val_arr[0].get('value', at_val_arr[0].get('體感溫度', t_val))))
                    else: at_val = t_val
                except: at_val = t_val
                
                try:
                    if wx_times:
                        wx_val_arr = wx_times[i].get('ElementValue', wx_times[i].get('elementValue', [{}]))
                        wx_val = wx_val_arr[0].get('Weather', wx_val_arr[0].get('value', wx_val_arr[0].get('天氣現象', '未知')))
                    else: wx_val = "未知"
                except: wx_val = "未知"
                
                parsed_data.append({
                    "regionName": region_name,
                    "dataDate": start_time,
                    "maxT": t_val,
                    "minT": at_val,
                    "weather": str(wx_val)
                })
    except Exception as e:
        print(f"解析 JSON 發生錯誤: {e}")
        
    return parsed_data
