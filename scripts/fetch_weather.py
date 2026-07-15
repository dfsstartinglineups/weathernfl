import os
import requests
import json
import firebase_admin
from firebase_admin import credentials, db

# 1. Initialize Firebase (Ensure FIREBASE_SERVICE_ACCOUNT is set in GitHub Secrets)
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

def fetch_nfl_schedule():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        data = requests.get(url, timeout=10).json()
        return data.get('events', [])
    except:
        return []

def fetch_open_meteo(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
    try:
        data = requests.get(url, timeout=10).json()
        return data.get('current', {})
    except:
        return {}

def main():
    print("🏈 Fetching ESPN NFL Schedule & Weather...")
    events = fetch_nfl_schedule()
    
    live_state = {}
    for event in events:
        game_id = event['id']
        comp = event['competitions'][0]
        home_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'home'), None)
        away_competitor = next((c for c in comp['competitors'] if c['homeAway'] == 'away'), None)
        
        home_abbr = home_competitor['team']['abbreviation'] if home_competitor else "TBD"
        
        stadium_info = stadiums_dict.get(home_abbr, None)
        weather_data = {"temperature_2m": 72, "wind_speed_10m": 0, "precipitation": 0} # Default Dome
        
        if stadium_info and stadium_info['roof'] != "Dome":
            weather_data = fetch_open_meteo(stadium_info['lat'], stadium_info['lon'])
            
        live_state[game_id] = {
            "game_info": event['name'],
            "status": event['status']['type']['state'],
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
        print("✅ Firebase updated successfully.")
    else:
        print("⚠️ Firebase not initialized. Skipping push.")

if __name__ == "__main__":
    main()
