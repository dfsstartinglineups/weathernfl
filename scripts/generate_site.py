import os
import sys
import json
import re
import requests
import datetime
from datetime import timezone, timedelta
import zoneinfo


EST_TZ = zoneinfo.ZoneInfo("America/New_York")

# ==========================================
# 1. PATH CONFIGURATION & MASTER DATA
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'scripts' else SCRIPT_DIR

DATA_DIR = os.path.join(ROOT_DIR, 'data')
VENUES_FILE = os.path.join(DATA_DIR, 'venues.json')
STADIUMS_FILE = os.path.join(DATA_DIR, 'stadiums.json')
TEAM_PAGES_DIR = os.path.join(ROOT_DIR, 'team_pages')
MAIN_INDEX_FILE = os.path.join(ROOT_DIR, 'index.html')
SITEMAP_FILE = os.path.join(ROOT_DIR, 'sitemap.xml')

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEAM_PAGES_DIR, exist_ok=True)

# Master list of all 32 NFL Teams
NFL_TEAMS = [
    {"id": "ARI", "slug": "arizona-cardinals", "name": "Arizona Cardinals", "stadium": "State Farm Stadium"},
    {"id": "ATL", "slug": "atlanta-falcons", "name": "Atlanta Falcons", "stadium": "Mercedes-Benz Stadium"},
    {"id": "BAL", "slug": "baltimore-ravens", "name": "Baltimore Ravens", "stadium": "M&T Bank Stadium"},
    {"id": "BUF", "slug": "buffalo-bills", "name": "Buffalo Bills", "stadium": "Highmark Stadium"},
    {"id": "CAR", "slug": "carolina-panthers", "name": "Carolina Panthers", "stadium": "Bank of America Stadium"},
    {"id": "CHI", "slug": "chicago-bears", "name": "Chicago Bears", "stadium": "Soldier Field"},
    {"id": "CIN", "slug": "cincinnati-bengals", "name": "Cincinnati Bengals", "stadium": "Paycor Stadium"},
    {"id": "CLE", "slug": "cleveland-browns", "name": "Cleveland Browns", "stadium": "Huntington Bank Field"},
    {"id": "DAL", "slug": "dallas-cowboys", "name": "Dallas Cowboys", "stadium": "AT&T Stadium"},
    {"id": "DEN", "slug": "denver-broncos", "name": "Denver Broncos", "stadium": "Empower Field at Mile High"},
    {"id": "DET", "slug": "detroit-lions", "name": "Detroit Lions", "stadium": "Ford Field"},
    {"id": "GB",  "slug": "green-bay-packers", "name": "Green Bay Packers", "stadium": "Lambeau Field"},
    {"id": "HOU", "slug": "houston-texans", "name": "Houston Texans", "stadium": "NRG Stadium"},
    {"id": "IND", "slug": "indianapolis-colts", "name": "Indianapolis Colts", "stadium": "Lucas Oil Stadium"},
    {"id": "JAX", "slug": "jacksonville-jaguars", "name": "Jacksonville Jaguars", "stadium": "EverBank Stadium"},
    {"id": "KC",  "slug": "kansas-city-chiefs", "name": "Kansas City Chiefs", "stadium": "GEHA Field at Arrowhead Stadium"},
    {"id": "LV",  "slug": "las-vegas-raiders", "name": "Las Vegas Raiders", "stadium": "Allegiant Stadium"},
    {"id": "LAC", "slug": "los-angeles-chargers", "name": "Los Angeles Chargers", "stadium": "SoFi Stadium"},
    {"id": "LAR", "slug": "los-angeles-rams", "name": "Los Angeles Rams", "stadium": "SoFi Stadium"},
    {"id": "MIA", "slug": "miami-dolphins", "name": "Miami Dolphins", "stadium": "Hard Rock Stadium"},
    {"id": "MIN", "slug": "minnesota-vikings", "name": "Minnesota Vikings", "stadium": "U.S. Bank Stadium"},
    {"id": "NE",  "slug": "new-england-patriots", "name": "New England Patriots", "stadium": "Gillette Stadium"},
    {"id": "NO",  "slug": "new-orleans-saints", "name": "New Orleans Saints", "stadium": "Caesars Superdome"},
    {"id": "NYG", "slug": "new-york-giants", "name": "New York Giants", "stadium": "MetLife Stadium"},
    {"id": "NYJ", "slug": "new-york-jets", "name": "New York Jets", "stadium": "MetLife Stadium"},
    {"id": "PHI", "slug": "philadelphia-eagles", "name": "Philadelphia Eagles", "stadium": "Lincoln Financial Field"},
    {"id": "PIT", "slug": "pittsburgh-steelers", "name": "Pittsburgh Steelers", "stadium": "Acrisure Stadium"},
    {"id": "SF",  "slug": "san-francisco-49ers", "name": "San Francisco 49ers", "stadium": "Levi's Stadium"},
    {"id": "SEA", "slug": "seattle-seahawks", "name": "Seattle Seahawks", "stadium": "Lumen Field"},
    {"id": "TB",  "slug": "tampa-bay-buccaneers", "name": "Tampa Bay Buccaneers", "stadium": "Raymond James Stadium"},
    {"id": "TEN", "slug": "tennessee-titans", "name": "Tennessee Titans", "stadium": "Nissan Stadium"},
    {"id": "WSH", "slug": "washington-commanders", "name": "Washington Commanders", "stadium": "Northwest Stadium"}
]

# ==========================================
# 2. UTILITY & HELPERS
# ==========================================
def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)

def get_short_team_name(full_name):
    if not full_name or full_name == "TBD": return "TBD"
    parts = full_name.split()
    return parts[-1]

def load_json(path, default_val):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return default_val

# ==========================================
# 3. WEATHER FETCHING ENGINE
# ==========================================
def fetch_weather_api_hourly(lat, lon, game_iso_time, days_diff):
    if not WEATHER_API_KEY:
        return None

    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))
    req_days = max(1, min(14, days_diff + 2))
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days={req_days}&aqi=no&alerts=no"

    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return None
        
        data = res.json()
        current_data = data.get('current', {})
        current_epoch = int(datetime.datetime.now(timezone.utc).timestamp())
        
        all_hours = []
        for day in data.get('forecast', {}).get('forecastday', []):
            all_hours.extend(day.get('hour', []))
            
        target_epoch = int(utc_time.replace(minute=0, second=0, microsecond=0).timestamp())
        
        # Search for exact hour. If missing (due to API day limits), return None to force fallback.
        start_idx = next((i for i, h in enumerate(all_hours) if h['time_epoch'] == target_epoch), None)
        if start_idx is None:
            return None

        actual_start = max(0, start_idx - 1)
        actual_end = min(len(all_hours), start_idx + 4)

        hourly_slice = []
        for i in range(actual_start, actual_end):
            hour = all_hours[i]
            chance = hour.get('chance_of_rain', 0)
            condition_text = hour.get('condition', {}).get('text', '').lower()
            
            is_thunder = "thunder" in condition_text and "possible" not in condition_text
            is_snow = any(x in condition_text for x in ["snow", "ice", "blizzard", "sleet"])

            is_current_hour = (hour['time_epoch'] <= current_epoch < hour['time_epoch'] + 3600)
            if is_current_hour and current_data:
                curr_precip = current_data.get('precip_in', 0)
                curr_condition = current_data.get('condition', {}).get('text', '').lower()

                is_heavy_rain_text = any(x in curr_condition for x in ["heavy rain", "moderate rain", "torrential", "thunderstorm"])
                is_light_rain_text = "rain" in curr_condition and "possible" not in curr_condition and "patchy" not in curr_condition

                if curr_precip > 0.01 or is_heavy_rain_text or (is_light_rain_text and curr_precip > 0):
                    chance = 100
                elif curr_precip > 0:
                    chance = max(chance, 50)

                if "thunder" in curr_condition and "possible" not in curr_condition: is_thunder = True
                if any(x in curr_condition for x in ["snow", "ice", "blizzard", "sleet"]): is_snow = True

            hour_iso = datetime.datetime.fromtimestamp(hour['time_epoch'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

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
        print(f"⚠️ WeatherAPI Fetch Error: {e}")
        return None

def fetch_open_meteo_hourly(lat, lon, game_iso_time):
    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))
    game_date_str = utc_time.strftime('%Y-%m-%d')
    next_day = (utc_time + timedelta(days=1)).strftime('%Y-%m-%d')

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch",
        "timezone": "GMT", "start_date": game_date_str, "end_date": next_day
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200: return None
        
        data = res.json()
        current = data.get('current', {})
        time_array = data.get('hourly', {}).get('time', [])
        target_time_str = utc_time.strftime('%Y-%m-%dT%H:00')
        
        try: start_idx = time_array.index(target_time_str)
        except ValueError: start_idx = 1

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
        print(f"⚠️ Open-Meteo Fetch Error: {e}")
        return None

def fetch_game_weather(lat, lon, game_iso_time):
    utc_time = datetime.datetime.fromisoformat(game_iso_time.replace('Z', '+00:00'))
    today_utc = datetime.datetime.now(timezone.utc).date()
    days_diff = (utc_time.date() - today_utc).days

    if days_diff > 14 or days_diff < -1:
        return {"status": "too_early", "temp": "--", "windSpeed": 0, "precip": 0, "hourly": []}

    if days_diff <= 3:
        weather = fetch_weather_api_hourly(lat, lon, game_iso_time, days_diff)
        if weather: return weather
        return fetch_open_meteo_hourly(lat, lon, game_iso_time)
    else:
        weather = fetch_open_meteo_hourly(lat, lon, game_iso_time)
        if weather: return weather
        return {"status": "error", "temp": "--", "windSpeed": 0, "precip": 0, "hourly": []}

# ==========================================
# 4. SCHEDULE & GAME DATA FETCHING
# ==========================================
def get_week_label(stype, wk):
    if stype == 1: return f"Preseason Week {wk}"
    elif stype == 2: return f"Week {wk}"
    elif stype == 3: return f"Postseason Week {wk}"
    return f"Week {wk}"

def get_current_nfl_schedule(venues_dict):
    now = datetime.datetime.now()
    season_year = now.year if now.month > 2 else now.year - 1
    
    stype = 2
    wk = 1
    
    try:
        base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        data = requests.get(base_url, timeout=10).json()
        stype = data.get('season', {}).get('type', 2)
        wk = data.get('week', {}).get('number', 1)
    except Exception as e:
        print(f"⚠️ ESPN Scoreboard fetch error: {e}")

    week_label = get_week_label(stype, wk)
    schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season_year}&seasontype={stype}&week={wk}"
    
    games_list = []
    try:
        res_data = requests.get(schedule_url, timeout=10).json()
        events = res_data.get('events', [])
        
        # --- AUTO-ADVANCE WEEK CHECK ---
        # If ALL games in ESPN's active week are FINAL ('post'), automatically bump to the next week
        all_final = len(events) > 0 and all(e.get('status', {}).get('type', {}).get('state') == 'post' for e in events)
        
        if all_final:
            print(f"🏁 All games for {week_label} are FINAL. Automatically advancing to the next week's slate...")
            if stype == 1 and wk >= 4:
                stype, wk = 2, 1
            elif stype == 2 and wk >= 18:
                stype, wk = 3, 1
            else:
                wk += 1

            week_label = get_week_label(stype, wk)
            schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season_year}&seasontype={stype}&week={wk}"
            res_data = requests.get(schedule_url, timeout=10).json()
            events = res_data.get('events', [])
        # -------------------------------

        # --- GAME DAY FREQUENCY CHECK ---
        import zoneinfo
        import sys
        
        est_tz = zoneinfo.ZoneInfo("America/New_York")
        now_est = datetime.datetime.now(est_tz)
        
        is_game_day = False
        for event in events:
            game_time = event['date']
            g_dt = datetime.datetime.fromisoformat(game_time.replace('Z', '+00:00')).astimezone(est_tz)
            if g_dt.date() == now_est.date():
                is_game_day = True
                break
                
        if not is_game_day:
            # Only execute if the current minute is near the 0, 15, 30, or 45 mark
            if now_est.minute % 15 >= 5:
                print(f"💤 Non-game day. Time is {now_est.strftime('%I:%M %p')} EST. Skipping run to enforce 15-minute interval.")
                sys.exit(0)
        else:
            print(f"🏈 Game Day Detected! Executing 5-minute update cycle for {week_label}.")
        # --------------------------------
        
        for event in events:
            game_id = event['id']
            comp = event['competitions'][0]
            game_time = event['date']
            
            espn_venue = comp.get('venue', {})
            venue_id = str(espn_venue.get('id', ''))
            stadium_info = venues_dict.get(venue_id)
            
            if not stadium_info:
                is_indoor = espn_venue.get('indoor', False)
                stadium_info = {
                    "name": espn_venue.get('fullName', 'TBD Location'),
                    "city": espn_venue.get('address', {}).get('city', ''),
                    "state": espn_venue.get('address', {}).get('state', ''),
                    "roof": "Dome" if is_indoor else "Open",
                    "surface": "TBD",
                    "lat": 0.0, "lon": 0.0
                }
            
            is_dome = stadium_info['roof'] in ["Dome", "Retractable"]
            if not is_dome and stadium_info['lat'] != 0.0:
                weather_payload = fetch_game_weather(stadium_info['lat'], stadium_info['lon'], game_time) or {"status": "ok", "temp": 72, "windSpeed": 0, "precip": 0, "hourly": []}
            else:
                weather_payload = {"status": "ok", "temp": 70, "windSpeed": 0, "precip": 0, "hourly": []}

            home_comp = next((c for c in comp['competitors'] if c['homeAway'] == 'home'), None)
            away_comp = next((c for c in comp['competitors'] if c['homeAway'] == 'away'), None)

            home_abbr = home_comp['team']['abbreviation'] if home_comp else "TBD"
            away_abbr = away_comp['team']['abbreviation'] if away_comp else "TBD"
            if home_abbr == "WAS": home_abbr = "WSH"
            if away_abbr == "WAS": away_abbr = "WSH"

            games_list.append({
                "game_id": game_id,
                "game_info": event['name'],
                "status": event['status']['type']['state'],
                "clock": event['status']['type'].get('shortDetail', ''),
                "game_time": game_time,
                "week_label": week_label,
                "home_id": home_abbr,
                "away_id": away_abbr,
                "home_team": home_comp['team']['displayName'] if home_comp else "TBD",
                "away_team": away_comp['team']['displayName'] if away_comp else "TBD",
                "stadium": stadium_info,
                "weather": weather_payload
            })
    except Exception as e:
        print(f"❌ Failed to fetch current schedule: {e}")

    return week_label, games_list

# ==========================================
# 5. CARD HTML GENERATORS
# ==========================================
def generate_matchup_analysis(w, is_dome):
    if is_dome:
        return "✅ <b>Dome Environment:</b> Controlled climate with zero weather impact. Perfect passing conditions."
    
    # Check the hourly array so the text matches the card's percentage display
    hourly_list = w.get('hourly', [])
    max_pop = max([h.get('precipChance', 0) for h in hourly_list], default=0) if hourly_list else 0
    is_thunderstorm = any(h.get('isThunderstorm', False) for h in hourly_list) if hourly_list else False
    is_snow = any(h.get('isSnow', False) for h in hourly_list) if hourly_list else False
    
    notes = []
    wind = w.get('windSpeed', 0)
    precip = w.get('precip', 0)
    temp = w.get('temp', 70)

    # Trigger severe weather alerts
    if is_thunderstorm:
        notes.append("⚡ <b>Lightning Risk:</b> Thunderstorms in the area. Possibility of in-game weather delays.")
    if is_snow:
        notes.append("🌨️ <b>Snow Conditions:</b> Slippery footing, reduced visibility, and tough kicking conditions. Expect a run-heavy script.")

    # Trigger warnings based on actual rain accumulation OR a 30%+ probability
    if wind >= 15 and (precip > 0 or max_pop >= 30) and not is_snow:
        notes.append("🚨 <b>Heavy Weather:</b> Passing and kicking severely downgraded. Expect a run-heavy script.")
    elif wind >= 15:
        notes.append("💨 <b>High Winds:</b> Deep passing and long field goals downgraded.")
    elif (precip > 0 or max_pop >= 30) and not is_snow and not is_thunderstorm:
        notes.append("🌧️ <b>Wet Conditions:</b> Potential for sloppy play, fumbles, and dropped passes.")
    
    if temp >= 85: notes.append("🔥 <b>Heat Alert:</b> High temperatures could lead to player fatigue late in the game.")
    if temp <= 32: notes.append("❄️ <b>Freezing:</b> Cold weather typically favors the ground game and lowers total scoring.")
    
    if not notes:
        return "✅ <b>Neutral:</b> Fair weather conditions. No significant weather impact."
    return "<br>".join(notes)

def render_game_card(game, is_single_team=False):
    stadium = game.get('stadium', {})
    is_dome = stadium.get('roof') in ["Dome", "Retractable"]
    w = game.get('weather') or {"status": "too_early", "temp": "--", "windSpeed": 0, "precip": 0}
    is_too_early = w.get('status') == "too_early" or w.get('temp') == "--"
    
    # Extract 5-hour forecast window metrics
    hourly_list = w.get('hourly', [])
    max_pop = max([h.get('precipChance', 0) for h in hourly_list], default=0) if hourly_list else 0
    is_thunderstorm = any(h.get('isThunderstorm', False) for h in hourly_list) if hourly_list else False
    is_snow = any(h.get('isSnow', False) for h in hourly_list) if hourly_list else False

    border_class = ""
    bg_class = "bg-weather-sunny"
    precip_val = w.get('precip', 0)
    wind_val = w.get('windSpeed', 0)
    temp_val = w.get('temp', 70)

    # Severe Weather: Red Border & Animated Storm Gradient
    if is_too_early:
        bg_class = "bg-light"
    elif is_dome:
        bg_class = "bg-weather-roof"
    elif is_thunderstorm or is_snow or max_pop >= 60 or precip_val >= 0.25 or wind_val >= 20:
        border_class = "border-danger border-3"
        bg_class = "bg-weather-storm"
    # Moderate Weather: Yellow Border & Animated Rain Gradient
    elif max_pop >= 30 or precip_val > 0 or wind_val >= 15:
        border_class = "border-warning border-3"
        bg_class = "bg-weather-rain"
    # Breezy / Overcast: Cloudy Gradient
    elif wind_val >= 12 or max_pop >= 15:
        bg_class = "bg-weather-cloudy"

    # Time / Status Badge
    badge_text = "TBD"
    badge_style = "bg-light text-dark border"
    status_state = game.get('status', 'pre')

    if status_state == 'pre' and game.get('game_time'):
        dt = datetime.datetime.fromisoformat(game['game_time'].replace('Z', '+00:00')).astimezone(EST_TZ)
        badge_text = dt.strftime("%a %I:%M %p").replace(" 0", " ")
    elif status_state == 'in':
        badge_text = game.get('clock', 'LIVE')
        badge_style = "bg-danger text-white border-danger"
    elif status_state == 'post':
        badge_text = "FINAL"
        badge_style = "bg-secondary text-white border-secondary"

    away_short = get_short_team_name(game.get('away_team'))
    home_short = get_short_team_name(game.get('home_team'))
    away_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{game.get('away_id', '').lower()}.png"
    home_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{game.get('home_id', '').lower()}.png"

    display_rain = "0%" if is_dome else f"{max_pop}%"
    weather_emoji_line = f"Roof Closed 🌡️{temp_val}°" if is_dome else f"🌧️{display_rain} 🌡️{temp_val}° 💨{wind_val}mph"
    if is_too_early:
        weather_emoji_line = "Roof Closed" if is_dome else "🔭 Forecast pending..."

    stadium_name = stadium.get('name', 'TBD Location')
    stadium_lat = stadium.get('lat', 39.0)
    stadium_lon = stadium.get('lon', -95.0)
    surface_type = stadium.get('surface', '-')
    
    # Dynamic Surface Emoji: Tire (🛞) for Artificial/Turf, Seedling (🌱) for Natural Grass
    surface_lower = str(surface_type).lower()
    surface_emoji = "⚫" if ("turf" in surface_lower or "synthetic" in surface_lower or "astro" in surface_lower or "matrix" in surface_lower) else "🌱"

    radar_url = f"https://embed.windy.com/embed2.html?lat={stadium_lat}&lon={stadium_lon}&detailLat={stadium_lat}&detailLon={stadium_lon}&width=650&height=450&zoom=11&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=mph&metricTemp=%C2%B0F&radarRange=-1"

    if is_too_early:
        weather_section = """
            <div class="text-center p-3 mt-2 border-top">
                <h6 class="text-muted mb-1">🔭 Too Early to Forecast</h6>
                <p class="small text-muted mb-0" style="font-size: 0.75rem;">Accurate forecasts available ~14 days before kickoff.</p>
            </div>
        """
    else:
        hourly_html = ''
        if is_dome:
            hourly_html = '<div class="text-center mt-2"><small class="text-muted">Indoor Conditions Controlled</small></div>'
        elif w.get('hourly'):
            hours_markup = []
            for h in w['hourly'][:5]:
                ts = h.get('timestamp')
                dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(EST_TZ) if ts else datetime.datetime.now(EST_TZ)
                hr12 = dt.strftime("%I%p").lstrip("0")
                is_night = dt.hour >= 20 or dt.hour < 6
                
                pop = h.get('precipChance', 0)
                icon = '☀️'
                if pop >= 30:
                    icon = '⛈️' if h.get('isThunderstorm') else ('🌨️' if h.get('isSnow') else '🌧️')
                elif pop > 0:
                    icon = '⛅'
                elif is_night:
                    icon = '🌙'

                pop_str = f"{pop}%" if pop >= 20 else "&nbsp;"
                hours_markup.append(f'''
                    <div class="hour-card">
                        <div class="hour-time">{hr12}</div>
                        <div class="hour-icon">{icon}</div>
                        <div class="hour-pop">{pop_str}</div>
                        <div class="hour-temp">{h.get("temp", "--")}°</div>
                    </div>
                ''')
            hourly_html = f'<div class="hourly-scroll-container">{"".join(hours_markup)}</div>'

        weather_section = f"""
            <div class="weather-row row text-center align-items-center mt-2 mx-0">
                <div class="col-3 border-end px-1"><div class="fw-bold">{temp_val}°F</div><div class="small text-muted" style="font-size: 0.7rem;">Temp</div></div>
                <div class="col-3 border-end px-1"><div class="fw-bold text-dark">{surface_emoji}</div><div class="small text-muted" style="font-size: 0.7rem;">{surface_type}</div></div>
                <div class="col-3 border-end px-1"><div class="fw-bold text-primary" style="white-space: nowrap;">{display_rain}</div><div class="small text-muted" style="font-size: 0.7rem;">Rain</div></div>
                <div class="col-3 px-1"><div class="fw-bold">{wind_val} <span style="font-size:0.7em">mph</span></div><span class="wind-badge bg-secondary text-white" style="font-size: 0.55rem; white-space: nowrap; display: inline-block; padding: 2px 4px;">💨</span></div>
            </div>
            {hourly_html}
            <div class="mt-2 mb-2">
                <button class="btn btn-sm btn-outline-primary w-100 py-1 fw-bold" style="font-size: 0.8rem;" onclick="showRadar('{radar_url}', '{stadium_name}')">🗺️ View Live Radar Map</button>
            </div>
            <div class="analysis-box">
                <span class="analysis-title">✨ Weather Impact</span>
                {generate_matchup_analysis(w, is_dome)}
            </div>
        """

    col_class = "w-100 mb-3" if is_single_team else "col-md-6 col-lg-4 col-xl-3 mb-3 px-1"
    
    # Default State Logic
    show_ribbon = "none" if is_single_team else "block"
    show_full = "block" if is_single_team else "none"
    
    return f"""
    <div class="{col_class}" id="game-{game['game_id']}">
        <div class="card game-card shadow-sm {border_class} {bg_class}" style="overflow: hidden;">
            
            <!-- RIBBON VIEW -->
            <div class="ribbon-view p-2 position-relative" onclick="toggleSingleCard(event, '{game['game_id']}')" style="cursor: pointer; display: {show_ribbon};">
                <div class="d-flex align-items-center mb-1">
                    <span class="badge {badge_style} flex-shrink-0 px-2 py-1" style="font-size: 0.65rem;">{badge_text}</span>
                    <div class="fw-bold text-dark text-center flex-grow-1 ms-2" style="font-size: 0.75rem; letter-spacing: 0.2px;">
                        {weather_emoji_line}
                    </div>
                </div>
                <div class="d-flex align-items-center mt-1" style="gap: 4px;">
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="{away_logo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">{away_short}</span>
                    </div>
                    <span class="fw-bold text-muted flex-shrink-0 lh-1" style="font-size: 0.7rem;">@</span>
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="{home_logo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">{home_short}</span>
                    </div>
                    <div class="text-truncate text-end fw-bold flex-grow-1 ms-1" style="font-size: 0.7rem; opacity: 0.75;">{stadium_name}</div>
                </div>
            </div>

            <!-- FULL CARD VIEW -->
            <div class="full-card-view" onclick="toggleSingleCard(event, '{game['game_id']}')" style="cursor: pointer; display: {show_full};">
                <div class="card-body px-2 pt-2 pb-2"> 
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge {badge_style}">{badge_text}</span>
                        <span class="stadium-name text-truncate text-end flex-grow-1 ms-2" style="font-size: 0.8rem; font-weight: 600;">{stadium_name}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center px-1 mb-1">
                        <div class="d-flex align-items-center text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="{away_logo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain;" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate" style="font-size: 0.95rem;">{away_short}</div>
                        </div>
                        <div class="text-center text-muted fw-bold" style="width: 10%; font-size: 0.8rem;">@</div>
                        <div class="d-flex align-items-center justify-content-end text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="{home_logo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain;" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate text-end" style="font-size: 0.95rem;">{home_short}</div>
                        </div>
                    </div>
                    {weather_section}
                </div>
            </div>

        </div>
    </div>
    """

    
def render_bye_card(team_name, stadium_name):
    return f"""
    <div class="w-100 mb-3">
        <div class="card p-4 text-center border rounded bg-white shadow-sm">
            <h5 class="fw-bold text-dark mb-2">🏈 Bye Week / Off Week</h5>
            <p class="text-muted mb-0" style="font-size: 0.9rem;">
                The <b>{team_name}</b> do not have a game scheduled for this week.
            </p>
            <p class="text-muted small mt-2 mb-0">Home Venue: {stadium_name}</p>
        </div>
    </div>
    """

# ==========================================
# 6. HTML MASTER TEMPLATES
# ==========================================
MAIN_SITE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-QYCQBXBBJ7"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-QYCQBXBBJ7');
    </script>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{week_label} NFL Weather & Stadium Conditions | Live Fantasy & Betting Impacts</title>
    <meta name="description" content="Live NFL weather forecasts, wind speeds, turf conditions, and stadium roof status for {week_label}. Optimize your fantasy football and DFS lineups.">
    <meta name="keywords" content="NFL weather, fantasy football weather, DFS weather, NFL stadium turf, NFL betting conditions, live wind speed NFL">
    <link rel="canonical" href="https://weathernfl.com/">
    
    <meta property="og:title" content="Live NFL Weather & Turf Conditions - Weather NFL">
    <meta property="og:description" content="Check live wind speeds, rain forecasts, and stadium roof status before locking your fantasy football lineups.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://weathernfl.com/">
    <meta property="og:image" content="https://weathernfl.com/social-share.png">
    
    <meta name="twitter:card" content="summary">
    <meta name="twitter:site" content="@weathernfldaily">
    <meta name="twitter:creator" content="@weathernfldaily">
    <meta name="twitter:title" content="Live NFL Weather & Turf Conditions - Weather NFL">
    <meta name="twitter:description" content="Check live wind speeds, rain forecasts, and stadium roof status before locking your fantasy football lineups.">
    <meta name="twitter:image" content="https://weathernfl.com/social-share.png">
    
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Weather NFL",
      "url": "https://weathernfl.com/",
      "description": "Live NFL weather, wind, and turf conditions for sports bettors and fantasy players."
    }}
    </script>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <style>
        body {{ background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }} 
        .main-container {{ max-width: 1200px; margin: 30px auto; padding: 0 15px; }}
        .game-card {{ border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white; overflow: hidden; transition: transform 0.2s; }}
        .weather-row {{ font-size: 0.9rem; border-top: 1px solid #f1f3f5; padding-top: 8px; margin-top: 8px; padding-bottom: 4px; }}
        .stadium-name {{ color: #6c757d; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .wind-badge {{ font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; font-weight: 600; display: inline-block; }}
        .analysis-box {{ background-color: rgba(255, 255, 255, 0.6); border-left: 4px solid #0d6efd; padding: 8px 12px; margin-top: 12px; font-size: 0.8rem; color: #495057; line-height: 1.4; border-radius: 0 4px 4px 0; }}
        .analysis-title {{ font-weight: 800; text-transform: uppercase; font-size: 0.7rem; color: #0d6efd; display: block; margin-bottom: 4px; letter-spacing: 0.5px; }}
        .hourly-scroll-container {{ display: flex; overflow-x: auto; gap: 8px; padding: 8px 4px; margin-top: 8px; border-top: 1px solid rgba(0,0,0,0.05); scrollbar-width: thin; }}
        .hour-card {{ display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 60px; text-align: center; }}
        .hour-time {{ font-size: 0.75rem; font-weight: 600; color: #6c757d; margin-bottom: 2px; }}
        .hour-icon {{ font-size: 1.3rem; line-height: 1; margin-bottom: 2px; }}
        .hour-pop {{ font-size: 0.65rem; color: #5ac8fa; font-weight: 700; line-height: 1; height: 12px; margin-bottom: 2px; }}
        .hour-temp {{ font-size: 0.85rem; font-weight: 600; color: #212529; line-height: 1; }}

        @keyframes weather-flow {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
        .bg-weather-sunny {{ background: linear-gradient(-45deg, #e3f2fd, #e1f5fe, #f1f8e9); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }}
        .bg-weather-cloudy {{ background: linear-gradient(-45deg, #f5f5f5, #e0e0e0, #eeeeee); background-size: 300% 300%; animation: weather-flow 20s ease infinite; }}
        .bg-weather-rain {{ background: linear-gradient(180deg, #e3f2fd, #cfd8dc, #eceff1); background-size: 200% 200%; animation: weather-flow 8s ease infinite; }}
        .bg-weather-storm {{ background: linear-gradient(-45deg, #e1bee7, #cfd8dc, #e0e0e0); background-size: 300% 300%; animation: weather-flow 10s ease infinite; }}
        .bg-weather-snow {{ background: linear-gradient(-45deg, #f3e5f5, #e3f2fd, #ffffff); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }}
        .bg-weather-roof {{ background-color: #ffffff; }}
    </style>
</head>
<body>
    
    <nav class="navbar shadow-sm py-2 mb-0 sticky-top" style="background-color: #0f172a;">
        <div class="container d-flex justify-content-between align-items-center flex-wrap gap-2">
            <a href="/" class="navbar-brand text-white fw-bold m-0" style="font-style: italic; font-size: 1.6rem;">
                Weather <span style="color: #5ac8fa;">NFL</span>
            </a>
            <div class="d-flex align-items-center gap-2">
                <select id="team-nav-select" class="form-select form-select-sm fw-bold shadow-sm" style="background-color: #1e293b; color: #adb5bd; border: 1px solid #334155; cursor: pointer; max-width: 180px;" onchange="if(this.value) window.location.href=this.value;">
                    <option value="">Select Team</option>
                    {select_options}
                </select>
                <a href="/" class="btn btn-sm btn-outline-light px-3 fw-bold" style="font-size: 0.75rem;">
                    Full Slate
                </a>
            </div>
        </div>
    </nav>

    <div class="main-container">
        <div class="text-center mb-2">
            <h1 class="fw-bold h2 mb-1">Live NFL Weather & Stadium Conditions</h1>
            <div class="fw-bold text-secondary mb-2" style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                📅 {week_label}
            </div>
            <p class="text-muted mb-3" style="font-size: 0.85rem;">Tracking wind, rain, and turf impacts for fantasy and betting.</p>
            
            <div class="d-flex justify-content-center mb-3">
                <button class="btn btn-sm shadow-sm fw-bold px-4 py-1 border border-secondary" style="background-color: #fff; color: #495057; border-radius: 20px;" onclick="toggleAllWeatherCards()">
                    <span id="expand-toggle-icon">▼</span> 
                    <span id="expand-toggle-text">Expand All Cards</span>
                </button>
            </div>
        </div>
        
        <div id="games-container" class="row">
            {cards_content}
        </div>
    </div>

    <!-- LIVE RADAR MODAL -->
    <div class="modal fade" id="radarModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content shadow">
                <div class="modal-header bg-dark text-white border-0 py-2">
                    <h5 class="modal-title fw-bold" style="font-size: 1rem;">Live Weather Radar</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-0 bg-light" style="height: 60vh;">
                    <iframe id="radarFrame" src="" class="w-100 h-100 border-0" allowfullscreen></iframe>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    let globalScoreboardMode = true;

    function toggleSingleCard(e, gameId) {{
        if (e && e.target.closest('a, button, input, label, select')) return; 
        const card = document.getElementById(`game-${{gameId}}`);
        if (!card) return;
        
        const ribbon = card.querySelector('.ribbon-view');
        const full = card.querySelector('.full-card-view');
        
        if (ribbon.style.display === 'none') {{
            ribbon.style.display = 'block';
            full.style.display = 'none';
        }} else {{
            ribbon.style.display = 'none';
            full.style.display = 'block';
        }}
    }}

    function toggleAllWeatherCards() {{
        globalScoreboardMode = !globalScoreboardMode;
        const btnText = document.getElementById('expand-toggle-text');
        const btnIcon = document.getElementById('expand-toggle-icon');
        if (btnText && btnIcon) {{
            btnText.innerText = globalScoreboardMode ? 'Expand All Cards' : 'Collapse All Cards';
            btnIcon.innerText = globalScoreboardMode ? '▼' : '▲';
        }}
        
        document.querySelectorAll('.game-card').forEach(card => {{
            const ribbon = card.querySelector('.ribbon-view');
            const full = card.querySelector('.full-card-view');
            if (ribbon && full) {{
                ribbon.style.display = globalScoreboardMode ? 'block' : 'none';
                full.style.display = globalScoreboardMode ? 'none' : 'block';
            }}
        }});
    }}

    function showRadar(url, venueName) {{
        const modalElement = document.getElementById('radarModal');
        const modalTitle = document.querySelector('#radarModal .modal-title');
        const iframe = document.getElementById('radarFrame');
        if (modalTitle) modalTitle.innerText = `Radar: ${{venueName}}`;
        
        const myModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        if (iframe) iframe.src = '';
        
        const loadMap = function () {{
            if(iframe) iframe.src = url; 
            modalElement.removeEventListener('shown.bs.modal', loadMap); 
        }};
        modalElement.addEventListener('shown.bs.modal', loadMap);
        myModal.show();
    }}
    </script>
</body>
</html>
"""

TEAM_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-QYCQBXBBJ7"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-QYCQBXBBJ7');
    </script>
    
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    
    <meta name="description" content="{meta_desc}">
    <meta name="keywords" content="{team_name} weather, {stadium_name} wind direction, {stadium_name} rain delay, {team_name} game weather today, fantasy football weather, NFL weather">
    <link rel="canonical" href="https://weathernfl.com/team_pages/{team_slug}/" />
    
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_desc}">
    <meta property="og:url" content="https://weathernfl.com/team_pages/{team_slug}/">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://weathernfl.com/social-share.png">
    
    <meta name="twitter:card" content="summary">
    <meta name="twitter:site" content="@weathernfldaily">
    <meta name="twitter:creator" content="@weathernfldaily">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_desc}">
    <meta name="twitter:image" content="https://weathernfl.com/social-share.png">
    
    <script type="application/ld+json">
{schema_json}
    </script>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <style>
        body {{ background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }} 
        .main-container {{ max-width: 520px; margin: 30px auto; padding: 0 15px; }}
        .game-card {{ border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white; overflow: hidden; transition: transform 0.2s; }}
        .weather-row {{ font-size: 0.9rem; border-top: 1px solid #f1f3f5; padding-top: 8px; margin-top: 8px; padding-bottom: 4px; }}
        .stadium-name {{ color: #6c757d; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .wind-badge {{ font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; font-weight: 600; display: inline-block; }}
        .analysis-box {{ background-color: rgba(255, 255, 255, 0.6); border-left: 4px solid #0d6efd; padding: 8px 12px; margin-top: 12px; font-size: 0.8rem; color: #495057; line-height: 1.4; border-radius: 0 4px 4px 0; }}
        .analysis-title {{ font-weight: 800; text-transform: uppercase; font-size: 0.7rem; color: #0d6efd; display: block; margin-bottom: 4px; letter-spacing: 0.5px; }}
        .hourly-scroll-container {{ display: flex; overflow-x: auto; gap: 8px; padding: 8px 4px; margin-top: 8px; border-top: 1px solid rgba(0,0,0,0.05); scrollbar-width: thin; }}
        .hour-card {{ display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 60px; text-align: center; }}
        .hour-time {{ font-size: 0.75rem; font-weight: 600; color: #6c757d; margin-bottom: 2px; }}
        .hour-icon {{ font-size: 1.3rem; line-height: 1; margin-bottom: 2px; }}
        .hour-pop {{ font-size: 0.65rem; color: #5ac8fa; font-weight: 700; line-height: 1; height: 12px; margin-bottom: 2px; }}
        .hour-temp {{ font-size: 0.85rem; font-weight: 600; color: #212529; line-height: 1; }}

        @keyframes weather-flow {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
        .bg-weather-sunny {{ background: linear-gradient(-45deg, #e3f2fd, #e1f5fe, #f1f8e9); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }}
        .bg-weather-cloudy {{ background: linear-gradient(-45deg, #f5f5f5, #e0e0e0, #eeeeee); background-size: 300% 300%; animation: weather-flow 20s ease infinite; }}
        .bg-weather-rain {{ background: linear-gradient(180deg, #e3f2fd, #cfd8dc, #eceff1); background-size: 200% 200%; animation: weather-flow 8s ease infinite; }}
        .bg-weather-storm {{ background: linear-gradient(-45deg, #e1bee7, #cfd8dc, #e0e0e0); background-size: 300% 300%; animation: weather-flow 10s ease infinite; }}
        .bg-weather-snow {{ background: linear-gradient(-45deg, #f3e5f5, #e3f2fd, #ffffff); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }}
        .bg-weather-roof {{ background-color: #ffffff; }}
    </style>
</head>
<body>
    <nav class="navbar shadow-sm py-2 mb-0 sticky-top" style="background-color: #0f172a;">
        <div class="container d-flex justify-content-between align-items-center flex-wrap gap-2">
            <a href="/" class="navbar-brand text-white fw-bold m-0" style="font-style: italic; font-size: 1.6rem;">
                Weather <span style="color: #5ac8fa;">NFL</span>
            </a>
            
            <div class="d-flex align-items-center gap-2">
                <select id="team-nav-select" class="form-select form-select-sm fw-bold" style="background-color: #1e293b; color: #adb5bd; border: 1px solid #334155; cursor: pointer; max-width: 180px;" onchange="if(this.value) window.location.href=this.value;">
                    <option value="">Switch Team</option>
                    {select_options}
                </select>
                <a href="/" class="btn btn-sm btn-outline-light px-3 fw-bold" style="font-size: 0.75rem;">
                    Full Slate
                </a>
            </div>
        </div>
    </nav>
    
    <div class="main-container">
        <div class="text-center mt-3 mb-3">
            <h1 class="h4 fw-bold text-dark mb-1">{team_name} Weather Forecast</h1>
            <p class="text-muted mb-0" style="font-size: 0.85rem;">{stadium_name}</p>
        </div>
        <div id="team-weather-container">
            {team_card_content}
        </div>
    </div>
    
    <!-- LIVE RADAR MODAL -->
    <div class="modal fade" id="radarModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content shadow">
                <div class="modal-header bg-dark text-white border-0 py-2">
                    <h5 class="modal-title fw-bold" style="font-size: 1rem;">Live Weather Radar</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-0 bg-light" style="height: 60vh;">
                    <iframe id="radarFrame" src="" class="w-100 h-100 border-0" allowfullscreen></iframe>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const selectMenu = document.getElementById("team-nav-select");
            if (selectMenu) {{
                selectMenu.value = `/team_pages/{team_slug}/`;
            }}
        }});
        
        function toggleSingleCard(e, gameId) {{
            if (e && e.target.closest('a, button, input, label, select')) return; 
            const card = document.getElementById(`game-${{gameId}}`);
            if (!card) return;
            
            const ribbon = card.querySelector('.ribbon-view');
            const full = card.querySelector('.full-card-view');
            
            if (ribbon.style.display === 'none') {{
                ribbon.style.display = 'block';
                full.style.display = 'none';
            }} else {{
                ribbon.style.display = 'none';
                full.style.display = 'block';
            }}
        }}

        function showRadar(url, venueName) {{
            const modalElement = document.getElementById('radarModal');
            const modalTitle = document.querySelector('#radarModal .modal-title');
            const iframe = document.getElementById('radarFrame');
            if (modalTitle) modalTitle.innerText = `Radar: ${{venueName}}`;
            
            const myModal = bootstrap.Modal.getOrCreateInstance(modalElement);
            if (iframe) iframe.src = '';
            
            const loadMap = function () {{
                if(iframe) iframe.src = url; 
                modalElement.removeEventListener('shown.bs.modal', loadMap); 
            }};
            modalElement.addEventListener('shown.bs.modal', loadMap);
            myModal.show();
        }}
    </script>
</body>
</html>
"""

# ==========================================
# 7. SITEMAP & INDEXNOW GENERATOR
# ==========================================
def write_if_changed(filepath, new_content):
    """Compares new HTML against existing HTML. Writes and returns True only if changed."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            old_content = f.read()
        if old_content == new_content:
            return False
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True
def generate_sitemap(changed_urls):
    urls_with_paths = [
        ("https://weathernfl.com/", MAIN_INDEX_FILE)
    ]
    for team in sorted(NFL_TEAMS, key=lambda x: x["name"]):
        urls_with_paths.append((
            f"https://weathernfl.com/team_pages/{team['slug']}/",
            os.path.join(TEAM_PAGES_DIR, team['slug'], "index.html")
        ))

    sitemap_entries = []
    for i, (url, filepath) in enumerate(urls_with_paths):
        priority = "1.0" if i == 0 else "0.8"
        
        # Extract the real OS-level modification time for accurate SEO timestamps
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            dt = datetime.datetime.fromtimestamp(mtime, timezone.utc)
            lastmod = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            lastmod = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        sitemap_entries.append(
            f"  <url>\n"
            f"    <loc>{url}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>hourly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_entries) +
        '\n</urlset>'
    )

    with open(SITEMAP_FILE, 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)
    print("✅ Generated sitemap.xml using actual file modification dates!")

    # Ping IndexNow only with URLs that actually changed
    if not changed_urls:
        print("ℹ️ No HTML changes detected. Skipping IndexNow ping.")
        return

    indexnow_key = "3da3e81feb6d41e69defd45253bbe4dc"
    payload = {
        "host": "weathernfl.com",
        "key": indexnow_key,
        "keyLocation": f"https://weathernfl.com/{indexnow_key}.txt",
        "urlList": changed_urls
    }
    
    try:
        res = requests.post("https://api.indexnow.org/indexnow", json=payload, timeout=10)
        if res.status_code in [200, 202]:
            print(f"🚀 Successfully pinged IndexNow with {len(changed_urls)} modified URLs!")
        else:
            print(f"⚠️ IndexNow ping failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"⚠️ IndexNow ping exception: {e}")

# ==========================================
# 8. MAIN CONTROLLER PIPELINE
# ==========================================
def main():
    now_utc = datetime.datetime.now(timezone.utc)
    now_iso = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"🎬 Starting NFL Weather Static Site Generator ({now_iso})...")

    # Load venues database
    venues_dict = load_json(VENUES_FILE, {})
    stadiums_list = load_json(STADIUMS_FILE, [])

    # Step 1: Fetch Schedule & Weather for Current Week Only
    week_label, games = get_current_nfl_schedule(venues_dict)
    print(f"🏈 Fetched {len(games)} games for {week_label}.")

    # Step 2: Build Dropdown Select Options
    sorted_teams = sorted(NFL_TEAMS, key=lambda x: x["name"])
    select_options = "\n".join([f'                    <option value="/team_pages/{t["slug"]}/">{t["name"]}</option>' for t in sorted_teams])

    # Track which URLs actually received new HTML
    changed_urls = []

    # Step 3: Render Main index.html
    main_cards_html = []
    if games:
        for g in games:
            main_cards_html.append(render_game_card(g, is_single_team=False))
        cards_content = "\n".join(main_cards_html)
    else:
        cards_content = f'''
        <div class="col-12 text-center py-5">
            <div class="alert alert-light border shadow-sm">
                <h5>No Games Scheduled for {week_label}</h5>
            </div>
        </div>
        '''

    main_html = MAIN_SITE_TEMPLATE.format(
        week_label=week_label,
        select_options=select_options,
        cards_content=cards_content
    )

    if write_if_changed(MAIN_INDEX_FILE, main_html):
        changed_urls.append("https://weathernfl.com/")
        print("✅ Main index.html updated.")
    else:
        print("⏭️ Main index.html unchanged. Skipped write.")

    # Step 4: Render All 32 Team Pages
    for team in NFL_TEAMS:
        team_id = team["id"]
        team_name = team["name"]
        team_slug = team["slug"]

        target_game = None
        for g in games:
            h_id = g['home_id'].upper()
            a_id = g['away_id'].upper()
            if h_id in [team_id, "WAS" if team_id == "WSH" else team_id] or a_id in [team_id, "WAS" if team_id == "WSH" else team_id]:
                target_game = g
                break

        if target_game:
            card_markup = render_game_card(target_game, is_single_team=True)
            is_home = target_game['home_id'].upper() in [team_id, "WAS" if team_id == "WSH" else team_id]
            opp_name = target_game['away_team'] if is_home else target_game['home_team']
            stadium_name = target_game.get('stadium', {}).get('name', team['stadium'])
            stadium_city = target_game.get('stadium', {}).get('city', '')
            stadium_state = target_game.get('stadium', {}).get('state', '')

            matchup_title = f"{team_name} vs {opp_name}" if is_home else f"{team_name} @ {opp_name}"
            page_title = f"{matchup_title} Weather Forecast at {stadium_name} | Rain & Wind Forecast"
            meta_desc = f"View the live weather forecast for the {matchup_title} game at {stadium_name}. Track real-time rain delay risks, stadium wind direction, hourly temperatures, and betting odds."
            og_title = f"{matchup_title} Game Weather at {stadium_name} - Weather NFL"
            og_desc = f"Track stadium wind, hourly rain risks, and weather impact analytics for the {matchup_title} game at {stadium_name}."
            schema_name = f"{matchup_title} Game"
            schema_address = f"{stadium_city}, {stadium_state}"
        else:
            stadium_name = team['stadium']
            card_markup = render_bye_card(team_name, stadium_name)

            page_title = f"{team_name} Game Weather at {stadium_name} | Rain & Wind Forecast"
            meta_desc = f"View the live weather forecast for the {team_name} game at {stadium_name}. Track real-time rain delay risks, stadium wind direction, hourly temperatures, and betting odds."
            og_title = f"{team_name} Game Weather at {stadium_name} - Weather NFL"
            og_desc = f"Track stadium wind, hourly rain risks, and weather impact analytics for the {team_name} game at {stadium_name}."
            schema_name = f"{team_name} Home Game"
            schema_address = stadium_name

        schema_dict = {
            "@context": "https://schema.org",
            "@type": "SportsEvent",
            "name": schema_name,
            "location": {
                "@type": "Place",
                "name": stadium_name,
                "address": schema_address
            }
        }
        schema_json = json.dumps(schema_dict, indent=4)

        team_html = TEAM_PAGE_TEMPLATE.format(
            page_title=page_title,
            meta_desc=meta_desc,
            team_name=team_name,
            stadium_name=stadium_name,
            team_slug=team_slug,
            og_title=og_title,
            og_desc=og_desc,
            schema_json=schema_json,
            select_options=select_options,
            team_card_content=card_markup
        )

        team_dir = os.path.join(TEAM_PAGES_DIR, team_slug)
        os.makedirs(team_dir, exist_ok=True)
        
        output_filepath = os.path.join(team_dir, "index.html")
        if write_if_changed(output_filepath, team_html):
            changed_urls.append(f"https://weathernfl.com/team_pages/{team_slug}/")

    print(f"🚀 HTML parsing complete. {len(changed_urls)} pages required updates.")

    # Step 5: Build sitemap.xml and Ping
    generate_sitemap(changed_urls)
    print("🎉 Static site generation pipeline complete!")

if __name__ == "__main__":
    main()
