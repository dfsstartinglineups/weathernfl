import os
import requests
import json
import datetime
import firebase_admin
from firebase_admin import credentials, db

# 🔑 Read WeatherAPI Key securely from environment variables
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")

# 1. Initialize Firebase 
if not firebase_admin._apps:
    raw_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if raw_key:
        cred = credentials.Certificate(json.loads(raw_key))
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://nbastartingfive-8b420-default-rtdb.firebaseio.com/'})

# 2. Load Venues Data
venues_dict = {}
try:
    with open('data/venues.json', 'r') as f:
        venues_dict = json.load(f)
except FileNotFoundError:
    print("⚠️ data/venues.json not found! Proceeding with API fallbacks.")

# --- WEATHER API PROVIDERS ---

def fetch_weather_api_hourly(lat, lon, game_iso_time, days_diff):
    """WeatherAPI.com fetcher for high-accuracy near-term games (<= 3 days away)."""
    if not WEATHER_API_KEY:
        print("⚠️ WEATHER_API_KEY environment variable is missing!")
        return None

    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))

    # WeatherAPI forecast days needed
    req_days = max(1, min(14, days_diff + 2))
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days={req_days}&aqi=no&alerts=no"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ WeatherAPI returned status code {response.status_code}")
            return None
        
        data = response.json()
        current_data = data.get('current', {})
        current_epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        
        all_hours = []
        for day in data.get('forecast', {}).get('forecastday', []):
            all_hours.extend(day.get('hour', []))
            
        target_epoch = int(utc_time.replace(minute=0, second=0, microsecond=0).timestamp())
        
        # Find index matching kickoff hour
        start_idx = next((i for i, h in enumerate(all_hours) if h['time_epoch'] == target_epoch), 0)

        # Slice 5-hour window: 1 hr before kickoff to 3 hrs after
        actual_start = max(0, start_idx - 1)
        actual_end = min(len(all_hours), start_idx + 4)

        hourly_slice = []
        for i in range(actual_start, actual_end):
            hour = all_hours[i]
            chance = hour.get('chance_of_rain', 0)
            condition_text = hour.get('condition', {}).get('text', '').lower()
            
            is_thunder = "thunder" in condition_text and "possible" not in condition_text
            is_snow = any(x in condition_text for x in ["snow", "ice", "blizzard", "sleet"])

            # Current hour physical station override
            is_current_hour = (hour['time_epoch'] <= current_epoch < hour['time_epoch'] + 3600)
            if is_current_hour and current_data:
                curr_precip = current_data.get('precip_in', 0)
                curr_condition = current_data.get('condition', {}).get('text', '').lower()

                # Strict rain override rules
                is_heavy_rain_text = any(x in curr_condition for x in ["heavy rain", "moderate rain", "torrential", "thunderstorm"])
                is_light_rain_text = "rain" in curr_condition and not "possible" in curr_condition and not "patchy" in curr_condition

                if curr_precip > 0.01 or is_heavy_rain_text or (is_light_rain_text and curr_precip > 0):
                    chance = 100
                elif curr_precip > 0:
                    chance = max(chance, 50)

                if "thunder" in curr_condition and not "possible" in curr_condition:
                    is_thunder = True
                if any(x in curr_condition for x in ["snow", "ice", "blizzard", "sleet"]):
                    is_snow = True

            hour_iso = datetime.datetime.fromtimestamp(hour['time_epoch'], datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            hourly_slice.append({
                "timestamp": hour_iso,
                "temp": round(hour.get('temp_f', 72)),
                "precipChance": chance,
                "isThunderstorm": is_thunder,
                "isSnow": is_snow
            })

        kickoff_hour = all_hours[start_idx] if len(all_hours) > start_idx else (all_hours[0] if all_hours else {})
        
        return {
            "status": "ok",
            "temp": round(kickoff_hour.get('temp_f', 72)),
            "windSpeed": round(kickoff_hour.get('wind_mph', 0)),
            "precip": round(float(kickoff_hour.get('precip_in', 0.0)), 2),
            "hourly": hourly_slice
        }
        
    except Exception as e:
        print(f"   ⚠️ WeatherAPI Fetch Error: {e}")
        return None

def fetch_open_meteo_hourly(lat, lon, game_iso_time):
    """Open-Meteo fetcher for games farther out (4 to 14 days away)."""
    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))
    
    game_date_str = utc_time.strftime('%Y-%m-%d')
    next_day = (utc_time + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "GMT",
        "start_date": game_date_str,
        "end_date": next_day
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        current = data.get('current', {})
        time_array = data.get('hourly', {}).get('time', [])
        
        target_time_str = utc_time.strftime('%Y-%m-%dT%H:00')
        
        try:
            start_idx = time_array.index(target_time_str)
        except ValueError:
            start_idx = 1

        actual_start = max(0, start_idx - 1)
        actual_end = min(len(time_array), start_idx + 4)

        hourly_slice = []
        for i in range(actual_start, actual_end):
            code = data['hourly'].get("weather_code", [0])[i]
            is_thunder = code in [95, 96, 99]
            is_snow = code in [71, 73, 75, 77, 85, 86]
            
            temp_val = data['hourly'].get("temperature_2m", [72])[i]
            chance = data['hourly'].get("precipitation_probability", [0])[i]
            
            hourly_slice.append({
                "timestamp": time_array[i] + "Z",
                "temp": int(temp_val) if temp_val is not None else "--",
                "precipChance": chance if chance is not None else 0,
                "isThunderstorm": is_thunder,
                "isSnow": is_snow
            })
            
        target_temp = data['hourly'].get("temperature_2m", [72])[start_idx] if len(data['hourly'].get("temperature_2m", [])) > start_idx else current.get('temperature_2m', 72)

        return {
            "status": "ok",
            "temp": int(target_temp) if target_temp is not None else 72,
            "windSpeed": int(current.get('wind_speed_10m', 0)),
            "precip": round(float(current.get('precipitation', 0.0)), 2),
            "hourly": hourly_slice
        }
        
    except Exception as e:
        print(f"   ⚠️ Open-Meteo Fetch Error: {e}")
        return None

def fetch_game_weather(lat, lon, game_iso_time):
    """Hybrid Router: WeatherAPI for <= 3 days, Open-Meteo for > 3 days."""
    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))
    today_utc = datetime.datetime.now(datetime.timezone.utc).date()
    days_diff = (utc_time.date() - today_utc).days

    if days_diff > 14 or days_diff < 0:
        return {"status": "too_early", "temp": "--", "windSpeed": 0, "precip": 0, "hourly": []}

    # 🎯 <= 3 Days Away: WeatherAPI.com
    if days_diff <= 3:
        weather = fetch_weather_api_hourly(lat, lon, game_iso_time, days_diff)
        if weather:
            return weather
        print("   ⚠️ WeatherAPI failed, falling back to Open-Meteo...")
        return fetch_open_meteo_hourly(lat, lon, game_iso_time)

    # 🔭 > 3 Days Away: Open-Meteo
    else:
        weather = fetch_open_meteo_hourly(lat, lon, game_iso_time)
        if weather:
            return weather
        return {"status": "error", "temp": "--", "windSpeed": 0, "precip": 0, "hourly": []}

# --- MAIN LOGIC ---

def get_week_label(stype, wk):
    if stype == 1: return f"Preseason Week {wk}"
    elif stype == 2: return f"Week {wk}"
    elif stype == 3: return f"Postseason Week {wk}"
    return f"Week {wk}"

def get_current_nfl_week():
    now = datetime.datetime.now()
    season_year = now.year if now.month > 2 else now.year - 1
    
    if now.month in [7, 8]:
        return 1, 1, season_year
        
    try:
        base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        data = requests.get(base_url, timeout=10).json()
        stype = data.get('season', {}).get('type', 2)
        wk = data.get('week', {}).get('number', 1)
        return stype, wk, season_year
    except:
        return 2, 1, season_year

def main():
    print("🏈 Fetching ESPN NFL Schedule & Weather (Hybrid Router)...")
    
    current_season_type, current_week, season_year = get_current_nfl_week()
    next_season_type = current_season_type
    next_week = current_week + 1

    if current_season_type == 1 and current_week >= 4:
        next_season_type = 2
        next_week = 1
    elif current_season_type == 2 and current_week >= 18:
        next_season_type = 3
        next_week = 1

    fetches = [
        {
            "url": f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season_year}&seasontype={current_season_type}&week={current_week}",
            "label": get_week_label(current_season_type, current_week),
            "order": 1
        },
        {
            "url": f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season_year}&seasontype={next_season_type}&week={next_week}",
            "label": get_week_label(next_season_type, next_week),
            "order": 2
        }
    ]
    
    live_state = {}
    for fetch in fetches:
        try:
            data = requests.get(fetch["url"], timeout=10).json()
            events = data.get('events', [])
        except:
            events = []

        for event in events:
            game_id = event['id']
            comp = event['competitions'][0]
            game_time = event['date']
            
            espn_venue = comp.get('venue', {})
            venue_id = str(espn_venue.get('id', ''))
            stadium_info = venues_dict.get(venue_id)
            
            if not stadium_info:
                print(f"⚠️ Unknown Venue ID {venue_id} detected for game {game_id}. Using API fallback data.")
                is_indoor = espn_venue.get('indoor', False)
                stadium_info = {
                    "name": espn_venue.get('fullName', 'TBD Location'),
                    "city": espn_venue.get('address', {}).get('city', ''),
                    "state": espn_venue.get('address', {}).get('state', ''),
                    "roof": "Dome" if is_indoor else "Open",
                    "surface": "TBD",
                    "lat": 0.0,
                    "lon": 0.0
                }
            
            weather_payload = {"status": "ok", "temp": 72, "windSpeed": 0, "precip": 0, "hourly": []} 
            
            if stadium_info['roof'] not in ["Dome", "Retractable"] and stadium_info['lat'] != 0.0:
                api_weather = fetch_game_weather(stadium_info['lat'], stadium_info['lon'], game_time)
                if api_weather:
                    weather_payload = api_weather
            elif stadium_info['roof'] in ["Dome", "Retractable"]:
                weather_payload = {
                    "status": "ok",
                    "temp": 70,
                    "windSpeed": 0,
                    "precip": 0,
                    "hourly": []
                }
                
            home_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'home'), None)
            away_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'away'), None)
            
            home_abbr = home_competitor['team']['abbreviation'] if home_competitor else "TBD"
            away_abbr = away_competitor['team']['abbreviation'] if away_competitor else "TBD"
            
            live_state[game_id] = {
                "game_info": event['name'],
                "status": event['status']['type']['state'], 
                "game_time": game_time, 
                "clock": event['status']['type'].get('shortDetail', ''), 
                "week_label": fetch["label"],
                "week_order": fetch["order"],
                "home_id": home_abbr,
                "away_id": away_abbr,
                "home_team": home_competitor['team']['displayName'] if home_competitor else "TBD",
                "away_team": away_competitor['team']['displayName'] if away_competitor else "TBD",
                "stadium": stadium_info,
                "weather": weather_payload
            }
    
    if firebase_admin._apps:
        db.reference('nfl_weather').set(live_state)
        print(f"✅ Firebase updated successfully with {len(live_state)} games.")
    else:
        print("⚠️ Firebase not initialized. Skipping push.")

if __name__ == "__main__":
    main()
