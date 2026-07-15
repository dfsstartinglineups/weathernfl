import os
import requests
import json
import firebase_admin
from firebase_admin import credentials, db

# 1. Initialize Firebase 
if not firebase_admin._apps:
    raw_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if raw_key:
        cred = credentials.Certificate(json.loads(raw_key))
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://nbastartingfive-8b420-default-rtdb.firebaseio.com/'})

# 2. Load Stadium Data
stadiums_dict = {}
with open('data/stadiums.json', 'r') as f:
    stadiums = json.load(f)
    for s in stadiums:
        stadiums_dict[s['id']] = s

def fetch_open_meteo(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
    try:
        data = requests.get(url, timeout=10).json()
        return data.get('current', {})
    except:
        return {}

def get_week_label(stype, wk):
    if stype == 1: return f"Preseason Week {wk}"
    elif stype == 2: return f"Week {wk}"
    elif stype == 3: return f"Postseason Week {wk}"
    return f"Week {wk}"

def main():
    print("🏈 Fetching ESPN NFL Schedule (Current & Next Week) & Weather...")
    
    base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        base_data = requests.get(base_url, timeout=10).json()
    except Exception as e:
        print(f"Failed to reach ESPN API: {e}")
        return

    # Dynamically determine the current week from ESPN's global state
    current_season_type = base_data.get('season', {}).get('type', 2)
    current_week = base_data.get('week', {}).get('number', 1)

    # Calculate next week (handling season transitions)
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
            "url": f"{base_url}?seasontype={current_season_type}&week={current_week}",
            "label": get_week_label(current_season_type, current_week),
            "order": 1
        },
        {
            "url": f"{base_url}?seasontype={next_season_type}&week={next_week}",
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
            home_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'home'), None)
            away_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'away'), None)
            
            home_abbr = home_competitor['team']['abbreviation'] if home_competitor else "TBD"
            
            stadium_info = stadiums_dict.get(home_abbr, None)
            weather_data = {"temperature_2m": 72, "wind_speed_10m": 0, "precipitation": 0} 
            
            # Fetch weather (Note: if the game is 14 days out, Open-Meteo returns defaults, which is safely handled)
            if stadium_info and stadium_info['roof'] != "Dome":
                weather_data = fetch_open_meteo(stadium_info['lat'], stadium_info['lon'])
                
            live_state[game_id] = {
                "game_info": event['name'],
                "status": event['status']['type']['state'], 
                "game_time": event['date'], 
                "clock": event['status']['type'].get('shortDetail', ''), 
                "week_label": fetch["label"],
                "week_order": fetch["order"],
                "home_id": home_abbr,
                "away_id": away_competitor['team']['abbreviation'] if away_competitor else "TBD",
                "home_team": home_competitor['team']['displayName'] if home_competitor else "TBD",
                "away_team": away_competitor['team']['displayName'] if away_competitor else "TBD",
                "stadium": stadium_info,
                "weather": {
                    "temp": weather_data.get('temperature_2m', 72),
                    "windSpeed": weather_data.get('wind_speed_10m', 0),
                    "precip": weather_data.get('precipitation', 0)
                }
            }
    
    # Push straight to Firebase
    if firebase_admin._apps:
        db.reference('nfl_weather').set(live_state)
        print(f"✅ Firebase updated successfully with {len(live_state)} games across 2 weeks.")
    else:
        print("⚠️ Firebase not initialized. Skipping push.")

if __name__ == "__main__":
    main()
