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
    """抓取 O-A0005-001 紫外線觀測資料 (增強解析版)"""
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0005-001?Authorization={API_KEY}&format=JSON"
    uvi_dict = {}
    try:
        res = requests.get(url, verify=False)
        res.raise_for_status()
        data = res.json()
        
        # 兼容不同結構的 API 回傳格式
        locations = data.get('records', {}).get('weatherElement', {}).get('location', [])
        if not locations:
            locations = data.get('records', {}).get('location', [])

        for loc in locations:
            # 兼容數值欄位名稱
            uvi_val = loc.get('uvIndex', loc.get('value', 0))
            
            county = "未知"
            # 嘗試從 parameter 中尋找縣市名稱
            for p in loc.get('parameter', []):
                p_name = p.get('name', p.get('parameterName', ''))
                if p_name in ['CITY', 'COUNTYNAME', 'CITY_SN']:
                    county = p.get('value', p.get('parameterValue', '未知'))
                    break
            
            # 若找不到 CITY 欄位，直接用測站名稱推測
            if county == "未知":
                county = loc.get('locationName', '未知')

            if county != "未知":
                # 自動補齊「市」或「縣」
                if len(county) == 2 and county in ["臺北", "新北", "桃園", "臺中", "臺南", "高雄", "基隆", "新竹", "嘉義"]:
                    county += "市"
                elif len(county) == 2:
                    county += "縣"
                    
                county = county.replace('台', '臺')
                try:
                    current_val = float(uvi_val)
                    if county not in uvi_dict or current_val > uvi_dict[county]:
                        uvi_dict[county] = current_val # 保留該縣市最高數值
                except:
                    pass
    except Exception as e:
        print(f"UVI 取得失敗: {e}")
        
    return uvi_dict
