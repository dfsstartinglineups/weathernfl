import os
import json
import re
import firebase_admin
from firebase_admin import credentials, db

# ==========================================
# CONFIGURATION & FIREBASE INITIALIZATION
# ==========================================
if not firebase_admin._apps:
    raw_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if raw_key:
        cred = credentials.Certificate(json.loads(raw_key))
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://nbastartingfive-8b420-default-rtdb.firebaseio.com/'
        })
    else:
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://nbastartingfive-8b420-default-rtdb.firebaseio.com/'
            })
        except Exception as e:
            print(f"⚠️ Firebase credential loading failed: {e}. Falling back to default titles.")

def slugify(text):
    """Convert text into clean, SEO-friendly URL slug (e.g. 'Buffalo Bills' -> 'buffalo-bills')"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def get_live_schedule():
    """Fetches the live schedule directly from Firebase."""
    if not firebase_admin._apps:
        return {}
    try:
        ref = db.reference('nfl_weather')
        return ref.get() or {}
    except Exception as e:
        print(f"⚠️ Error pulling schedule from Firebase: {e}")
        return {}

def find_next_game(team_id, schedule):
    """
    Searches the live Firebase schedule to find the team's next game.
    Normalizes 'WAS' vs 'WSH' to avoid silent mismatches.
    """
    team_id_upper = team_id.upper()
    if team_id_upper == "WSH":
        team_id_upper = "WAS"
        
    games = []
    
    for game_id, g in schedule.items():
        home_id = g.get('home_id', '').upper()
        away_id = g.get('away_id', '').upper()
        
        # Normalize incoming Firebase IDs to match stadiums.json WSH standard
        if home_id == "WAS": home_id = "WSH"
        if away_id == "WAS": away_id = "WSH"
        
        if home_id == team_id.upper() or away_id == team_id.upper():
            games.append(g)
            
    if not games:
        return None
        
    # Sort games so current week (order 1) comes first
    games.sort(key=lambda x: x.get('week_order', 1))
    return games[0]

# ==========================================
# PRISTINE HTML MASTER TEMPLATE
# ==========================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-QYCQBXBBJ7"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-QYCQBXBBJ7');
    </script>
    
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__PAGE_TITLE__</title>
    
    <meta name="description" content="__META_DESC__">
    <meta name="keywords" content="__TEAM_NAME__ weather, __STADIUM_NAME__ wind direction, __STADIUM_NAME__ rain delay, __TEAM_NAME__ game weather today, fantasy football weather, NFL weather">
    <link rel="canonical" href="__CANONICAL_URL__" />
    
    <!-- OpenGraph / Social Meta -->
    <meta property="og:title" content="__OG_TITLE__">
    <meta property="og:description" content="__OG_DESC__">
    <meta property="og:url" content="__OG_URL__">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://weathernfl.com/social-share.png">
    
    <!-- Comprehensive Twitter Meta Tags (Compact Summary Mode) -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:site" content="@weathernfldaily">
    <meta name="twitter:creator" content="@weathernfldaily">
    <meta name="twitter:title" content="__TWITTER_TITLE__">
    <meta name="twitter:description" content="__TWITTER_DESC__">
    <meta name="twitter:image" content="https://weathernfl.com/social-share.png">
    
    <script type="application/ld+json">
__SCHEMA_JSON__
    </script>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-database-compat.js"></script>
    
    <style>
        body { background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; } 
        .main-container { max-width: 520px; margin: 30px auto; padding: 0 15px; }
        .game-card { border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white; overflow: hidden; }
        .weather-row { font-size: 0.9rem; border-top: 1px solid #f1f3f5; padding-top: 8px; margin-top: 8px; padding-bottom: 4px; }
        .stadium-name { color: #6c757d; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .wind-badge { font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; font-weight: 600; display: inline-block; }
        .analysis-box { background-color: rgba(255, 255, 255, 0.6); border-left: 4px solid #0d6efd; padding: 8px 12px; margin-top: 12px; font-size: 0.8rem; color: #495057; line-height: 1.4; border-radius: 0 4px 4px 0; }
        .analysis-title { font-weight: 800; text-transform: uppercase; font-size: 0.7rem; color: #0d6efd; display: block; margin-bottom: 4px; letter-spacing: 0.5px; }
        
        /* Hourly Forecast CSS */
        .hourly-scroll-container { display: flex; overflow-x: auto; gap: 8px; padding: 8px 4px; margin-top: 8px; border-top: 1px solid rgba(0,0,0,0.05); scrollbar-width: thin; }
        .hour-card { display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 60px; text-align: center; }
        .hour-time { font-size: 0.75rem; font-weight: 600; color: #6c757d; margin-bottom: 2px; }
        .hour-icon { font-size: 1.3rem; line-height: 1; margin-bottom: 2px; }
        .hour-pop { font-size: 0.65rem; color: #5ac8fa; font-weight: 700; line-height: 1; height: 12px; margin-bottom: 2px; }
        .hour-temp { font-size: 0.85rem; font-weight: 600; color: #212529; line-height: 1; }
        
        /* Flowing Weather Gradients */
        @keyframes weather-flow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .bg-weather-sunny { background: linear-gradient(-45deg, #e3f2fd, #e1f5fe, #f1f8e9); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }
        .bg-weather-cloudy { background: linear-gradient(-45deg, #f5f5f5, #e0e0e0, #eeeeee); background-size: 300% 300%; animation: weather-flow 20s ease infinite; }
        .bg-weather-rain { background: linear-gradient(180deg, #e3f2fd, #cfd8dc, #eceff1); background-size: 200% 200%; animation: weather-flow 8s ease infinite; }
        .bg-weather-storm { background: linear-gradient(-45deg, #e1bee7, #cfd8dc, #e0e0e0); background-size: 300% 300%; animation: weather-flow 10s ease infinite; }
        .bg-weather-snow { background: linear-gradient(-45deg, #f3e5f5, #e3f2fd, #ffffff); background-size: 300% 300%; animation: weather-flow 15s ease infinite; }
        .bg-weather-roof { background-color: #ffffff; }
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
__SELECT_OPTIONS__
                </select>
                <a href="/" class="btn btn-sm btn-outline-light px-3 fw-bold" style="font-size: 0.75rem;">
                    Full Slate
                </a>
            </div>
        </div>
    </nav>
    
    <div class="main-container">
        <div id="team-weather-container">
            <div class="text-center p-5 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading __TEAM_NAME__ forecast...
            </div>
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
    
    <script>
        window.TARGET_TEAM_ID = "__TEAM_ID__";
        document.addEventListener("DOMContentLoaded", () => {
            const selectMenu = document.getElementById("team-nav-select");
            if (selectMenu) {
                selectMenu.value = `/team_pages/__TEAM_SLUG__/`;
            }
        });
    </script>
    <script src="../../js/app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

# ==========================================
# MAIN GENERATION LOOP
# ==========================================
def main():
    print("🚀 Running NFL Weather SEO Page Generator...")

    # Load standard teams config
    try:
        with open('data/stadiums.json', 'r') as f:
            stadiums_list = json.load(f)
    except FileNotFoundError:
        print("❌ Error: data/stadiums.json not found!")
        return

    # Grab live schedule from Firebase
    live_schedule = get_live_schedule()

    # Create root team_pages directory if missing
    os.makedirs('team_pages', exist_ok=True)

    # 1. Generate Navigation Select Dropdown options
    select_options_html = ""
    for s in stadiums_list:
        team_slug = slugify(s['team'])
        select_options_html += f'                    <option value="/team_pages/{team_slug}/">{s["team"]}</option>\n'

    # 2. Loop through each team and generate its static index.html
    for s in stadiums_list:
        team_name = s['team']
        team_id = s['id']
        team_slug = slugify(team_name)
        
        # Check if they have a game scheduled
        game = find_next_game(team_id, live_schedule)
        
        if game:
            opponent_name = game['away_team'] if game['home_id'] == team_id.upper() or (game['home_id'] == 'WAS' and team_id.upper() == 'WSH') else game['home_team']
            is_home = game['home_id'] == team_id.upper() or (game['home_id'] == 'WAS' and team_id.upper() == 'WSH')
            stadium_name = game.get('stadium', {}).get('name', s['name'])
            stadium_city = game.get('stadium', {}).get('city', s.get('city', 'Home City'))
            stadium_state = game.get('stadium', {}).get('state', s.get('state', ''))
            
            # Create dynamic Title and Matchup tags
            if is_home:
                matchup_title = f"{team_name} vs {opponent_name}"
            else:
                matchup_title = f"{team_name} @ {opponent_name}"
                
            page_title = f"{matchup_title} Weather Forecast at {stadium_name} | Rain & Wind Forecast"
            meta_desc = f"View the live weather forecast for the {matchup_title} game at {stadium_name}. Track real-time rain delay risks, stadium wind direction, hourly temperatures, and betting odds."
            og_title = f"{matchup_title} Game Weather at {stadium_name} - Weather NFL"
            og_desc = f"Track stadium wind, hourly rain risks, and weather impact analytics for the {matchup_title} game at {stadium_name}."
            schema_name = f"{matchup_title} Game"
            schema_address = f"{stadium_city}, {stadium_state}"
        else:
            # Bye week / Off-season Fallback
            stadium_name = s['name']
            stadium_city = s.get('city', 'Home City')
            stadium_state = s.get('state', '')
            
            page_title = f"{team_name} Game Weather at {stadium_name} | Rain & Wind Forecast"
            meta_desc = f"View the live weather forecast for the {team_name} game at {stadium_name}. Track real-time rain delay risks, stadium wind direction, hourly temperatures, and betting odds."
            og_title = f"{team_name} Game Weather at {stadium_name} - Weather NFL"
            og_desc = f"Track stadium wind, hourly rain risks, and weather impact analytics for the {team_name} game at {stadium_name}."
            schema_name = f"{team_name} Home Game"
            schema_address = f"{stadium_city}, {stadium_state}"

        # Build schema json
        schema_data = {
            "@context": "https://schema.org",
            "@type": "SportsEvent",
            "name": schema_name,
            "location": {
                "@type": "Place",
                "name": stadium_name,
                "address": schema_address
            }
        }
        schema_json = json.dumps(schema_data, indent=4)

        # Assemble individual file content via clean placeholder mapping
        content = HTML_TEMPLATE
        content = content.replace("__PAGE_TITLE__", page_title)
        content = content.replace("__META_DESC__", meta_desc)
        content = content.replace("__TEAM_NAME__", team_name)
        content = content.replace("__STADIUM_NAME__", stadium_name)
        content = content.replace("__CANONICAL_URL__", f"https://weathernfl.com/team_pages/{team_slug}/")
        content = content.replace("__OG_TITLE__", og_title)
        content = content.replace("__OG_DESC__", og_desc)
        content = content.replace("__OG_URL__", f"https://weathernfl.com/team_pages/{team_slug}/")
        content = content.replace("__TWITTER_TITLE__", og_title)
        content = content.replace("__TWITTER_DESC__", og_desc)
        content = content.replace("__SCHEMA_JSON__", schema_json)
        content = content.replace("__SELECT_OPTIONS__", select_options_html)
        content = content.replace("__TEAM_ID__", team_id)
        content = content.replace("__TEAM_SLUG__", team_slug)

        # Create output directories
        team_dir = os.path.join("team_pages", team_slug)
        os.makedirs(team_dir, exist_ok=True)

        # Write clean output file
        output_filepath = os.path.join(team_dir, "index.html")
        with open(output_filepath, "w") as out_f:
            out_f.write(content)

    print("✅ All SEO pages generated successfully with their pristine styling preserved!")

if __name__ == "__main__":
    main()
