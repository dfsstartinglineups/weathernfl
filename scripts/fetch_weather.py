import os
import requests
import json
import datetime
import firebase_admin
from firebase_admin import credentials, db

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

def fetch_open_meteo_hourly(lat, lon, game_iso_time):
    """
    Fetches hourly weather forecasts and returns current kickoff weather 
    plus a structured 4-hour window starting at kickoff.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        current = data.get('current', {})
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        
        # Parse game time
        # ESPN sends e.g. "2026-09-10T20:20Z"
        game_dt = datetime.datetime.fromisoformat(game_iso_time.replace("Z", "+00:00"))
        
        # Find the index closest to kickoff
        start_idx = 0
        min_diff = float('inf')
        for idx, t_str in enumerate(times):
            t_dt = datetime.datetime.fromisoformat(t_str).replace(tzinfo=datetime.timezone.utc)
            diff = abs((t_dt - game_dt).total_seconds())
            if diff < min_diff:
                min_diff = diff
                start_idx = idx

        # Format a 4-hour forecast window for the app's scrollable hourly bar
        formatted_hourly = []
        for i in range(start_idx, min(start_idx + 4, len(times))):
            t_str = times[i]
            code = hourly.get("weather_code", [0])[i]
            
            # WMO Weather Interpretation Codes
            is_thunder = code in [95, 96, 99]
            is_snow = code in [71, 73, 75, 77, 85, 86]
            
            # Open-Meteo returns times as "YYYY-MM-DDTHH:MM" local. Convert to UTC ISO string
            local_dt = datetime.datetime.fromisoformat(t_str)
            utc_iso = local_dt.replace(tzinfo=datetime.timezone.utc).isoformat() + "Z"

            formatted_hourly.append({
                "timestamp": utc_iso,
                "temp": int(hourly.get("temperature_2m", [72])[i]),
                "precipChance": int(hourly.get("precipitation_probability", [0])[i]),
                "isThunderstorm": is_thunder,
                "isSnow": is_snow
            })
            
        return {
            "temp": int(current.get('temperature_2m', 72)),
            "windSpeed": int(current.get('wind_speed_10m', 0)),
            "precip": round(float(current.get('precipitation', 0.0)), 2),
            "hourly": formatted_hourly
        }
        
    except Exception as e:
        print(f"   ⚠️ Weather Fetch Error: {e}")
        return None

def get_week_label(stype, wk):
    if stype == 1: return f"Preseason Week {wk}"
    elif stype == 2: return f"Week {wk}"
    elif stype == 3: return f"Postseason Week {wk}"
    return f"Week {wk}"

def get_current_nfl_week():
    """
    Directly targets the correct Season Type based on the calendar month.
    July/Aug = Preseason (seasontype 1). Sept-Feb = Reg/Post (seasontype 2 or 3).
    """
    now = datetime.datetime.now()
    season_year = now.year if now.month > 2 else now.year - 1
    
    # If we are in July or August, explicitly force Preseason Week 1
    if now.month in [7, 8]:
        return 1, 1, season_year
        
    # Otherwise, let ESPN tell us the current active Regular/Post season week
    try:
        base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        data = requests.get(base_url, timeout=10).json()
        stype = data.get('season', {}).get('type', 2)
        wk = data.get('week', {}).get('number', 1)
        return stype, wk, season_year
    except:
        return 2, 1, season_year

def main():
    print("🏈 Fetching ESPN NFL Schedule & Weather...")
    
    # 1. Grab the exact active week and season type
    current_season_type, current_week, season_year = get_current_nfl_week()

    # 2. Calculate the "Next Week" for the UI toggle button
    next_season_type = current_season_type
    next_week = current_week + 1

    # Handle the transition from Preseason to Regular Season
    if current_season_type == 1 and current_week >= 4:
        next_season_type = 2
        next_week = 1
    elif current_season_type == 2 and current_week >= 18:
        next_season_type = 3
        next_week = 1

    # 3. Build the exact API URLs using the seasontype parameter
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
            
            # --- VENUE ID PIVOT LOGIC ---
            espn_venue = comp.get('venue', {})
            venue_id = str(espn_venue.get('id', ''))
            
            # Look up the venue by its ID in our new venues database
            stadium_info = venues_dict.get(venue_id)
            
            # Fallback if ESPN uses a new/unknown venue ID
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
            
            # Fetch Weather
            weather_payload = {"temp": 72, "windSpeed": 0, "precip": 0, "hourly": []} 
            
            # Fetch weather if it's an outdoor/retractable stadium and we have coordinates
            if stadium_info['roof'] not in ["Dome"] and stadium_info['lat'] != 0.0:
                api_weather = fetch_open_meteo_hourly(stadium_info['lat'], stadium_info['lon'], game_time)
                if api_weather:
                    weather_payload = api_weather
            else:
                # Controlled indoor climate template
                weather_payload = {
                    "temp": 70,
                    "windSpeed": 0,
                    "precip": 0,
                    "hourly": []
                }
                
            # Parse Teams
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
    
    # 4. Push directly to Firebase
    if firebase_admin._apps:
        db.reference('nfl_weather').set(live_state)
        print(f"✅ Firebase updated successfully with {len(live_state)} games.")
    else:
        print("⚠️ Firebase not initialized. Skipping push.")

if __name__ == "__main__":
    main()
