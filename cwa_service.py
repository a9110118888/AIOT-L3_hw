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
            
            t_elem = elements.get('溫度', {})
            at_elem = elements.get('體感溫度', {})
            wx_elem = elements.get('天氣現象', {})
            pop_elem = elements.get('3小時降雨機率', {}) # 🌟 新增：抓取降雨機率元素
            
            t_times = t_elem.get('Time', t_elem.get('time', []))
            at_times = at_elem.get('Time', at_elem.get('time', []))
            wx_times = wx_elem.get('Time', wx_elem.get('time', []))
            pop_times = pop_elem.get('Time', pop_elem.get('time', [])) # 🌟 新增：降雨機率時間陣列
            
            if not t_times: continue
            
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

                # 🌟 新增：精準抓取降雨機率 (若氣象署沒提供則預設為 0)
                try:
                    if pop_times and i < len(pop_times):
                        pop_val_arr = pop_times[i].get('ElementValue', pop_times[i].get('elementValue', [{}]))
                        pop_val_str = pop_val_arr[0].get('ProbabilityOfPrecipitation', pop_val_arr[0].get('value', '0'))
                        pop_val = int(pop_val_str) if str(pop_val_str).strip().isdigit() else 0
                    else: pop_val = 0
                except: pop_val = 0
                
                parsed_data.append({
                    "regionName": region_name,
                    "dataDate": start_time,
                    "maxT": t_val,
                    "minT": at_val,
                    "weather": str(wx_val),
                    "pop": pop_val  # 🌟 新增：把降雨機率存進字典
                })
    except Exception as e:
        print(f"解析 JSON 發生錯誤: {e}")
        
    return parsed_data

# --- 在 cwa_service.py 最下方新增這段 ---

def fetch_uvi_data():
    """改用最新 O-A0003-001 (即時天氣觀測) 抓取各縣市即時紫外線"""
    # 🌟 關鍵：將網址中的 O-A0005-001 改成了 O-A0003-001
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&format=JSON"
    uvi_dict = {}
    try:
        res = requests.get(url, verify=False)
        res.raise_for_status()
        data = res.json()
        
        # 氣象署最新 JSON 結構：records -> Station (陣列)
        stations = data.get('records', {}).get('Station', [])
        
        for st in stations:
            # 輕鬆取得縣市名稱
            county = st.get('GeoInfo', {}).get('CountyName', '未知')
            # 輕鬆取得即時紫外線指數
            uvi_val = st.get('WeatherElement', {}).get('UVIndex', -99)
            
            if county != "未知" and uvi_val != -99 and uvi_val is not None:
                county = county.replace('台', '臺') # 統一寫法
                try:
                    current_val = float(uvi_val)
                    # 排除儀器故障的無效值 (-99)，並取該縣市各測站中的最高 UVI
                    if current_val >= 0: 
                        if county not in uvi_dict or current_val > uvi_dict[county]:
                            uvi_dict[county] = current_val
                except:
                    pass
    except Exception as e:
        print(f"UVI 取得失敗: {e}")
        
    return uvi_dict
