import json
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
        links_html += f'<li><a class="dropdown-item" href="/team_pages/{team_slug}.html">{s["team"]} Weather</a></li>\n'

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
