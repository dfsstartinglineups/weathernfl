document.addEventListener('DOMContentLoaded', () => {
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
