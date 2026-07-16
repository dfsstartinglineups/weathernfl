import json
import os
import re

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def main():
    with open('data/stadiums.json', 'r', encoding='utf-8') as f:
        stadiums = json.load(f)

    os.makedirs('team_pages', exist_ok=True)
    
    # Generate index of links for the dropdown (MLB Style)
    links_html = ""
    for s in sorted(stadiums, key=lambda x: x['team']):
        team_slug = slugify(s['team'])
        links_html += f'                    <option value="/team_pages/{team_slug}/">{s["team"]}</option>\n'

    for s in stadiums:
        team_name = s['team']
        team_id = s['id']
        team_slug = slugify(team_name)
        stadium_name = s['name']
        roof_type = s['roof']
        surface = s['surface']

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{team_name} Game Weather at {stadium_name} | Rain & Wind Forecast</title>
    
    <meta name="description" content="View the live weather forecast for the {team_name} game at {stadium_name}. Track real-time rain delay risks, stadium wind direction, hourly temperatures, and betting odds.">
    <meta name="keywords" content="{team_name} weather, {stadium_name} wind direction, {stadium_name} rain delay, {team_name} game weather today, fantasy football weather, NFL weather">
    <link rel="canonical" href="https://weathernfl.com/team_pages/{team_slug}/" />
    
    <!-- OpenGraph / Social Meta -->
    <meta property="og:title" content="{team_name} Game Weather at {stadium_name} - Weather NFL">
    <meta property="og:description" content="Track stadium wind, hourly rain risks, and weather impact analytics for the {team_name} game at {stadium_name}.">
    <meta property="og:url" content="https://weathernfl.com/team_pages/{team_slug}/">
    <meta property="og:type" content="website">
    
    <!-- Twitter Meta Tags -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:site" content="@weathernfldaily">
    
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

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-database-compat.js"></script>
    
    <style>
        body {{ background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }} 
        .main-container {{ max-width: 520px; margin: 30px auto; padding: 0 15px; }}
        .game-card {{ border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white; overflow: hidden; }}
        .weather-row {{ font-size: 0.9rem; border-top: 1px solid #f1f3f5; padding-top: 8px; margin-top: 8px; padding-bottom: 4px; }}
        .stadium-name {{ color: #6c757d; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .wind-badge {{ font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; font-weight: 600; display: inline-block; }}
        .analysis-box {{ background-color: rgba(255, 255, 255, 0.6); border-left: 4px solid #0d6efd; padding: 8px 12px; margin-top: 12px; font-size: 0.8rem; color: #495057; line-height: 1.4; border-radius: 0 4px 4px 0; }}
        .analysis-title {{ font-weight: 800; text-transform: uppercase; font-size: 0.7rem; color: #0d6efd; display: block; margin-bottom: 4px; letter-spacing: 0.5px; }}
        
        /* Hourly Forecast CSS */
        .hourly-scroll-container {{ display: flex; overflow-x: auto; gap: 8px; padding: 8px 4px; margin-top: 8px; border-top: 1px solid rgba(0,0,0,0.05); scrollbar-width: thin; }}
        .hour-card {{ display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 60px; text-align: center; }}
        .hour-time {{ font-size: 0.75rem; font-weight: 600; color: #6c757d; margin-bottom: 2px; }}
        .hour-icon {{ font-size: 1.3rem; line-height: 1; margin-bottom: 2px; }}
        .hour-pop {{ font-size: 0.65rem; color: #5ac8fa; font-weight: 700; line-height: 1; height: 12px; margin-bottom: 2px; }}
        .hour-temp {{ font-size: 0.85rem; font-weight: 600; color: #212529; line-height: 1; }}

        /* Flowing Weather Gradients */
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
{links_html}
                </select>
                <a href="/" class="btn btn-sm btn-outline-light px-3 fw-bold" style="font-size: 0.75rem;">
                    Full Slate
                </a>
            </div>
        </div>
    </nav>

    <div class="main-container">
        <!-- Replaced row/col logic with MLB style isolated single-card container -->
        <div id="team-weather-container">
            <div class="text-center p-5 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading {team_name} forecast...
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
        // Set the global target team so app.js knows which games to filter
        window.TARGET_TEAM_ID = "{team_id}";
        
        document.addEventListener("DOMContentLoaded", () => {{
            const selectMenu = document.getElementById("team-nav-select");
            if (selectMenu) {{
                selectMenu.value = `/team_pages/{team_slug}/`;
            }}
        }});
    </script>
    <script src="../../js/app.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        
        # Create the team directory and write index.html inside it
        team_dir = os.path.join('team_pages', team_slug)
        os.makedirs(team_dir, exist_ok=True)
        filepath = os.path.join(team_dir, "index.html")
        
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(html_content)

    print(f"✅ Generated {len(stadiums)} SEO team folders/pages.")

if __name__ == "__main__":
    main()
