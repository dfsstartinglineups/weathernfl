import os
import json
import re
import firebase_admin
from firebase_admin import credentials, db

# ==========================================
# CONFIGURATION & FIREBASE INITIALIZATION
# ==========================================
# Initialize Firebase Admin SDK using your service account
if not firebase_admin._apps:
    raw_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if raw_key:
        cred = credentials.Certificate(json.loads(raw_key))
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://nbastartingfive-8b420-default-rtdb.firebaseio.com/'
        })
    else:
        # Fallback to local credential file if running locally
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
    Prioritizes 'Week 1' (or Order 1) over next week.
    """
    team_id_upper = team_id.upper()
    games = []
    
    for game_id, g in schedule.items():
        if g.get('home_id') == team_id_upper or g.get('away_id') == team_id_upper:
            games.append(g)
            
    if not games:
        return None
        
    # Sort games so current week (order 1) comes first
    games.sort(key=lambda x: x.get('week_order', 1))
    return games[0]

def main():
    print("🚀 Running SEO Page Generator...")

    # Load standard teams config
    try:
        with open('data/stadiums.json', 'r') as f:
            stadiums_list = json.load(f)
    except FileNotFoundError:
        print("❌ Error: data/stadiums.json not found!")
        return

    # Grab live schedule from Firebase
    live_schedule = get_live_schedule()

    # Create the build directory if it doesn't exist
    os.makedirs('build', exist_ok=True)

    # 1. Generate the dynamic links dropdown menu options
    links_html = ""
    for s in stadiums_list:
        team_slug = slugify(s['team'])
        links_html += f'<li><a class="dropdown-item" href="{team_slug}.html">{s["team"]}</a></li>\n'

    # 2. Loop through each team and generate its static HTML page
    for s in stadiums_list:
        team_name = s['team']
        team_id = s['id']
        team_slug = slugify(team_name)
        
        # Check if they have a game scheduled
        game = find_next_game(team_id, live_schedule)
        
        if game:
            opponent_name = game['away_team'] if game['home_id'] == team_id.upper() else game['home_team']
            is_home = game['home_id'] == team_id.upper()
            stadium_name = game.get('stadium', {}).get('name', s['name'])
            
            # Create the dynamic title and description strings
            if is_home:
                matchup_title = f"{team_name} vs {opponent_name}"
            else:
                matchup_title = f"{team_name} @ {opponent_name}"
                
            page_title = f"{matchup_title} Weather Forecast at {stadium_name} | NFL Weather"
            meta_desc = f"Get the real-time weather forecast, wind speeds, playing surface details, and matchup analysis for {matchup_title} at {stadium_name}. Plan your fantasy start/sit decisions!"
            header_title = f"Live Weather Forecast: {matchup_title}"
            header_subtitle = f"Playing at {stadium_name}"
        else:
            # Fallback title if there is a Bye Week or off-season
            page_title = f"{team_name} Weather Forecast at {s['name']} | NFL Weather"
            meta_desc = f"Real-time game day weather forecasts, wind speeds, playing surface, and stadium details for the {team_name} playing at {s['name']}."
            header_title = f"{team_name} Weather Forecast"
            header_subtitle = f"Home Field: {s['name']} (Roof: {s['roof']} | Surface: {s['surface']})"

        # HTML Template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <meta name="description" content="{meta_desc}">
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
    
    <!-- Firebase Libraries -->
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-database.js"></script>
    
    <!-- Dynamic ID Bridge to app.js -->
    <script>
        window.TARGET_TEAM_ID = "{team_id}";
    </script>
</head>
<body class="bg-light">

    <!-- Navbar / Header -->
    <nav class="navbar navbar-dark bg-dark shadow-sm">
        <div class="container d-flex justify-content-between align-items-center">
            <a class="navbar-brand fw-bold" href="index.html">🏈 NFL Weather</a>
            
            <!-- Teams Dropdown Menu -->
            <div class="dropdown">
                <button class="btn btn-outline-light btn-sm dropdown-toggle fw-bold" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    Change Team
                </button>
                <ul class="dropdown-menu dropdown-menu-end scrollable-menu" style="max-height: 300px; overflow-y: auto;">
                    {links_html}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content Container -->
    <div class="container my-4">
        <div class="text-center mb-4">
            <h1 class="fw-bold text-dark">{header_title}</h1>
            <p class="text-muted fs-6">{header_subtitle}</p>
        </div>

        <!-- This Container is Dynamically Populated by app.js from Firebase -->
        <div id="team-weather-container" class="row justify-content-center">
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading Game Forecasts...</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Windy Radar Modal -->
    <div class="modal fade" id="radarModal" tabindex="-1" aria-labelledby="radarModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title fw-bold" id="radarModalLabel">Live Radar</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-0" style="height: 450px;">
                    <iframe id="radarFrame" src="" width="100%" height="100%" frameborder="0"></iframe>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap & Custom Javascript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
"""

        # Write out the static file
        output_filepath = f"build/{team_slug}.html"
        with open(output_filepath, "w") as out_f:
            out_f.write(html_content)

    print("✅ All SEO pages generated successfully in the /build folder!")

if __name__ == "__main__":
    main()
