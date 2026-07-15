import os
import json

def scaffold_repository():
    print("🏈 Bootstrapping Complete NFL Weather Repository (No Workflows)...")

    # 1. Define Folder Structure
    directories = [
        "js",
        "scripts",
        "data",
        "team_pages"
    ]

    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"📁 Created directory: /{d}")

    # 2. Define File Contents
    
    # --- DATA: STADIUMS.JSON (Complete 32 NFL Teams) ---
    stadiums_data = [
        {"id": "ARI", "name": "State Farm Stadium", "team": "Arizona Cardinals", "lat": 33.5276, "lon": -112.2626, "roof": "Retractable", "surface": "Grass"},
        {"id": "ATL", "name": "Mercedes-Benz Stadium", "team": "Atlanta Falcons", "lat": 33.7553, "lon": -84.4006, "roof": "Retractable", "surface": "Turf"},
        {"id": "BAL", "name": "M&T Bank Stadium", "team": "Baltimore Ravens", "lat": 39.2780, "lon": -76.6227, "roof": "Open", "surface": "Grass"},
        {"id": "BUF", "name": "Highmark Stadium", "team": "Buffalo Bills", "lat": 42.7738, "lon": -78.7870, "roof": "Open", "surface": "Turf"},
        {"id": "CAR", "name": "Bank of America Stadium", "team": "Carolina Panthers", "lat": 35.2258, "lon": -80.8528, "roof": "Open", "surface": "Turf"},
        {"id": "CHI", "name": "Soldier Field", "team": "Chicago Bears", "lat": 41.8623, "lon": -87.6167, "roof": "Open", "surface": "Grass"},
        {"id": "CIN", "name": "Paycor Stadium", "team": "Cincinnati Bengals", "lat": 39.0955, "lon": -84.5161, "roof": "Open", "surface": "Turf"},
        {"id": "CLE", "name": "Huntington Bank Field", "team": "Cleveland Browns", "lat": 41.5061, "lon": -81.6995, "roof": "Open", "surface": "Grass"},
        {"id": "DAL", "name": "AT&T Stadium", "team": "Dallas Cowboys", "lat": 32.7473, "lon": -97.0945, "roof": "Retractable", "surface": "Turf"},
        {"id": "DEN", "name": "Empower Field at Mile High", "team": "Denver Broncos", "lat": 39.7439, "lon": -105.0201, "roof": "Open", "surface": "Grass"},
        {"id": "DET", "name": "Ford Field", "team": "Detroit Lions", "lat": 42.3400, "lon": -83.0456, "roof": "Dome", "surface": "Turf"},
        {"id": "GB", "name": "Lambeau Field", "team": "Green Bay Packers", "lat": 44.5013, "lon": -88.0622, "roof": "Open", "surface": "Grass"},
        {"id": "HOU", "name": "NRG Stadium", "team": "Houston Texans", "lat": 29.6847, "lon": -95.4107, "roof": "Retractable", "surface": "Turf"},
        {"id": "IND", "name": "Lucas Oil Stadium", "team": "Indianapolis Colts", "lat": 39.7601, "lon": -86.1639, "roof": "Retractable", "surface": "Turf"},
        {"id": "JAX", "name": "EverBank Stadium", "team": "Jacksonville Jaguars", "lat": 30.3239, "lon": -81.6373, "roof": "Open", "surface": "Grass"},
        {"id": "KC", "name": "GEHA Field at Arrowhead", "team": "Kansas City Chiefs", "lat": 39.0489, "lon": -94.4839, "roof": "Open", "surface": "Grass"},
        {"id": "LV", "name": "Allegiant Stadium", "team": "Las Vegas Raiders", "lat": 36.0909, "lon": -115.1833, "roof": "Dome", "surface": "Grass"},
        {"id": "LAC", "name": "SoFi Stadium", "team": "Los Angeles Chargers", "lat": 33.9534, "lon": -118.3387, "roof": "Dome", "surface": "Turf"},
        {"id": "LAR", "name": "SoFi Stadium", "team": "Los Angeles Rams", "lat": 33.9534, "lon": -118.3387, "roof": "Dome", "surface": "Turf"},
        {"id": "MIA", "name": "Hard Rock Stadium", "team": "Miami Dolphins", "lat": 25.9580, "lon": -80.2389, "roof": "Open", "surface": "Grass"},
        {"id": "MIN", "name": "U.S. Bank Stadium", "team": "Minnesota Vikings", "lat": 44.9735, "lon": -93.2575, "roof": "Dome", "surface": "Turf"},
        {"id": "NE", "name": "Gillette Stadium", "team": "New England Patriots", "lat": 42.0909, "lon": -71.2643, "roof": "Open", "surface": "Turf"},
        {"id": "NO", "name": "Caesars Superdome", "team": "New Orleans Saints", "lat": 29.9511, "lon": -90.0812, "roof": "Dome", "surface": "Turf"},
        {"id": "NYG", "name": "MetLife Stadium", "team": "New York Giants", "lat": 40.8128, "lon": -74.0742, "roof": "Open", "surface": "Turf"},
        {"id": "NYJ", "name": "MetLife Stadium", "team": "New York Jets", "lat": 40.8128, "lon": -74.0742, "roof": "Open", "surface": "Turf"},
        {"id": "PHI", "name": "Lincoln Financial Field", "team": "Philadelphia Eagles", "lat": 39.9008, "lon": -75.1675, "roof": "Open", "surface": "Grass"},
        {"id": "PIT", "name": "Acrisure Stadium", "team": "Pittsburgh Steelers", "lat": 40.4468, "lon": -80.0158, "roof": "Open", "surface": "Grass"},
        {"id": "SF", "name": "Levi's Stadium", "team": "San Francisco 49ers", "lat": 37.4032, "lon": -121.9698, "roof": "Open", "surface": "Grass"},
        {"id": "SEA", "name": "Lumen Field", "team": "Seattle Seahawks", "lat": 47.5952, "lon": -122.3316, "roof": "Open", "surface": "Turf"},
        {"id": "TB", "name": "Raymond James Stadium", "team": "Tampa Bay Buccaneers", "lat": 27.9759, "lon": -82.5033, "roof": "Open", "surface": "Grass"},
        {"id": "TEN", "name": "Nissan Stadium", "team": "Tennessee Titans", "lat": 36.1665, "lon": -86.7713, "roof": "Open", "surface": "Turf"},
        {"id": "WAS", "name": "Commanders Field", "team": "Washington Commanders", "lat": 38.9076, "lon": -76.8645, "roof": "Open", "surface": "Grass"}
    ]

    # --- SCRIPTS: GENERATE_WEATHER_PAGES.PY (SEO Page Builder) ---
    generate_weather_pages_py = '''import json
import os
import re

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def main():
    with open('data/stadiums.json', 'r', encoding='utf-8') as f:
        stadiums = json.load(f)

    os.makedirs('team_pages', exist_ok=True)
    
    # Generate index of links for the dropdown
    links_html = ""
    for s in sorted(stadiums, key=lambda x: x['team']):
        team_slug = slugify(s['team'])
        links_html += f'<li><a class="dropdown-item" href="/team_pages/{team_slug}.html">{s["team"]} Weather</a></li>\\n'

    for s in stadiums:
        team_name = s['team']
        team_slug = slugify(team_name)
        stadium_name = s['name']
        roof_type = s['roof']
        surface = s['surface']

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{team_name} Weather & {stadium_name} Conditions | NFL DFS</title>
    <meta name="description" content="Check the latest {team_name} weather conditions at {stadium_name}. Get live wind, rain, and turf data for daily fantasy sports and sports betting.">
    <meta name="keywords" content="{team_name} weather, {stadium_name} weather, NFL weather, fantasy football weather, DFS conditions">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-database-compat.js"></script>
    
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "SportsEvent",
      "name": "{team_name} Home Game",
      "location": {{
        "@type": "Place",
        "name": "{stadium_name}",
        "address": "{team_name} Home City"
      }}
    }}
    </script>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">Weather <span class="text-primary">NFL</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="teamDropdown" role="button" data-bs-toggle="dropdown">
                            Select Team
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end shadow" style="max-height: 400px; overflow-y: auto;">
                            {links_html}
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1 class="fw-bold text-dark">{team_name} Weather</h1>
            <p class="text-muted">Live conditions for <strong>{stadium_name}</strong> | Roof: {roof_type} | Surface: {surface}</p>
        </div>
        
        <div class="row justify-content-center">
            <div class="col-md-8 text-center" id="single-team-container" data-team="{s['id']}">
                <div class="spinner-border spinner-border-sm text-primary mb-2"></div><br>
                <span class="text-muted">Fetching live game data from Firebase...</span>
            </div>
        </div>
    </div>

    <script src="../js/app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        
        filepath = os.path.join('team_pages', f"{team_slug}.html")
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(html_content)

    print(f"✅ Generated {len(stadiums)} SEO team pages.")

if __name__ == "__main__":
    main()
'''

    # --- SCRIPTS: FETCH_WEATHER.PY (Firebase + ESPN API) ---
    fetch_weather_py = '''import os
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
'''

    # --- JS: APP.JS (Firebase Listener & NFL Logic) ---
    app_js = '''document.addEventListener('DOMContentLoaded', () => {
    console.log("🏈 Initializing NFL Weather App...");

    // 1. Initialize Firebase 
    const firebaseConfig = { databaseURL: "https://nbastartingfive-8b420-default-rtdb.firebaseio.com/" };
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    
    // 2. Listen to live updates from the Python script
    const db = firebase.database();
    db.ref('nfl_weather').on('value', (snapshot) => {
        const data = snapshot.val();
        
        const singleTeamContainer = document.getElementById('single-team-container');
        const mainContainer = document.getElementById('games-container');
        
        if(data) {
            if (singleTeamContainer) {
                // Filter for a specific team's page
                const targetTeamId = singleTeamContainer.getAttribute('data-team');
                const filteredGames = Object.values(data).filter(g => g.home_id === targetTeamId || g.away_id === targetTeamId);
                renderGames(filteredGames, singleTeamContainer);
            } else if (mainContainer) {
                // Render all games on main hub
                renderGames(Object.values(data), mainContainer);
            }
        } else {
            const noDataHtml = '<div class="col-12 text-center text-muted">No game data currently available.</div>';
            if (singleTeamContainer) singleTeamContainer.innerHTML = noDataHtml;
            if (mainContainer) mainContainer.innerHTML = noDataHtml;
        }
    });
});

function renderGames(gamesArray, container) {
    container.innerHTML = ''; // Clear loader
    
    if (gamesArray.length === 0) {
        container.innerHTML = '<div class="alert alert-light border">No active matchups for this team right now.</div>';
        return;
    }
    
    gamesArray.forEach(game => {
        // NFL Specific Logic
        let impactText = "✅ Clear Conditions";
        const wSpeed = game.weather.windSpeed || 0;
        const wPrecip = game.weather.precip || 0;
        
        if (game.stadium && game.stadium.roof === "Dome") {
            impactText = "🏟️ Dome Environment (Perfect Conditions)";
        } else {
            if (wSpeed >= 15 && wPrecip > 0) {
                impactText = "🚨 Heavy Weather: passing/kicking downgraded, boost RBs.";
            } else if (wSpeed >= 15) {
                impactText = "💨 High Winds: Deep passing & kicking downgraded.";
            } else if (wPrecip > 0) {
                impactText = "🌧️ Wet Conditions: Potential for sloppy play & turnovers.";
            }
        }
        
        const surfaceText = game.stadium ? game.stadium.surface : "Unknown";
        const stadiumName = game.stadium ? game.stadium.name : "TBD Location";
        
        const card = document.createElement('div');
        // If it's the main container, use grid columns. If it's a single team container, span 100%.
        card.className = container.id === 'games-container' ? "col-md-6 col-lg-4 mb-3" : "w-100 mb-3 text-start";
        card.innerHTML = `
            <div class="card shadow-sm p-3 border-dark h-100">
                <h6 class="fw-bold text-primary mb-1">${game.game_info}</h6>
                <p class="text-muted mb-2" style="font-size: 0.85rem;">📍 ${stadiumName} | 🌱 ${surfaceText}</p>
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <span class="badge bg-secondary">${game.status}</span>
                </div>
                <hr class="mt-0">
                <div class="d-flex justify-content-between mb-2 fw-bold text-dark">
                    <span>🌡️ ${game.weather.temp}°F</span>
                    <span>💨 ${wSpeed} mph</span>
                    <span>🌧️ ${wPrecip}"</span>
                </div>
                <div class="mt-auto p-2 bg-light border-start border-3 border-primary text-sm fw-bold">
                    ${impactText}
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}
'''

    # --- HTML: INDEX.HTML (Fully Optimized SEO) ---
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFL Weather & Stadium Conditions | Live Fantasy & Betting Impacts</title>
    
    <!-- Heavy SEO Tags -->
    <meta name="description" content="Live NFL weather forecasts, wind speeds, turf conditions, and stadium roof status for every game. Optimize your fantasy football and DFS lineups.">
    <meta name="keywords" content="NFL weather, fantasy football weather, DFS weather, NFL stadium turf, NFL betting conditions, live wind speed NFL">
    <link rel="canonical" href="https://weathernfl.com/">
    
    <!-- OpenGraph / Social Meta -->
    <meta property="og:title" content="Live NFL Weather & Turf Conditions">
    <meta property="og:description" content="Check live wind speeds, rain forecasts, and stadium roof status before locking your fantasy football lineups.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://weathernfl.com/">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Weather NFL",
      "url": "https://weathernfl.com/",
      "description": "Live NFL weather, wind, and turf conditions for sports bettors and fantasy players."
    }
    </script>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-database-compat.js"></script>
</head>
<body class="bg-light">
    
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">Weather <span class="text-primary">NFL</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="#">Teams Hub</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1 class="fw-bold h2">Live NFL Weather & Stadium Conditions</h1>
            <p class="text-muted">Tracking wind, rain, and turf impacts for fantasy and betting.</p>
        </div>
        
        <div id="games-container" class="row">
            <div class="col-12 text-center text-muted py-5">
                <div class="spinner-border spinner-border-sm text-primary mb-2"></div><br>
                Syncing with live database...
            </div>
        </div>
    </div>

    <script src="js/app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

    # 3. Write Files to Disk
    files_to_write = {
        "data/stadiums.json": json.dumps(stadiums_data, indent=4),
        "scripts/fetch_weather.py": fetch_weather_py,
        "scripts/generate_weather_pages.py": generate_weather_pages_py,
        "js/app.js": app_js,
        "index.html": index_html
    }

    for path, content in files_to_write.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Generated file: {path}")

    print("\n✅ Scaffold Complete! Your highly optimized core files are ready locally.")

if __name__ == "__main__":
    scaffold_repository()
