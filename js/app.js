// ==========================================
// STATE MANAGEMENT & FIREBASE
// ==========================================
let savedScoreboardState = localStorage.getItem('nflScoreboardMode');
let globalScoreboardMode = savedScoreboardState !== null ? savedScoreboardState === 'true' : true; 

document.addEventListener('DOMContentLoaded', () => {
    console.log("🏈 Initializing NFL Weather App...");

    // UI Toggle Initialization
    const toggleScoreboardBtn = document.getElementById('toggle-all-cards');
    if (toggleScoreboardBtn) {
        toggleScoreboardBtn.innerHTML = globalScoreboardMode ? '🔽 COMPACT SCOREBOARD' : '🔼 EXPAND ALL CARDS';
        
        toggleScoreboardBtn.addEventListener('click', () => {
            globalScoreboardMode = !globalScoreboardMode;
            localStorage.setItem('nflScoreboardMode', globalScoreboardMode);
            toggleScoreboardBtn.innerHTML = globalScoreboardMode ? '🔽 COMPACT SCOREBOARD' : '🔼 EXPAND ALL CARDS';
            
            const allRibbons = document.querySelectorAll('.ribbon-view');
            const allFulls = document.querySelectorAll('.full-view');
            
            if (globalScoreboardMode) {
                // Expanded Mode
                allRibbons.forEach(el => el.classList.add('d-none'));
                allFulls.forEach(el => el.classList.remove('d-none'));
            } else {
                // Compact Mode
                allRibbons.forEach(el => el.classList.remove('d-none'));
                allFulls.forEach(el => el.classList.add('d-none'));
            }
        });
    }

    // Initialize Firebase 
    const firebaseConfig = { databaseURL: "https://nbastartingfive-8b420-default-rtdb.firebaseio.com/" };
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    
    // Listen to live updates
    const db = firebase.database();
    db.ref('nfl_weather').on('value', (snapshot) => {
        const data = snapshot.val();
        const mainContainer = document.getElementById('games-container');
        
        if(data) {
            renderGames(Object.entries(data), mainContainer);
        } else {
            mainContainer.innerHTML = '<div class="col-12 text-center text-muted">No game data currently available.</div>';
        }
    });
});

// ==========================================
// CARD TOGGLING LOGIC
// ==========================================
window.toggleSingleCard = function(gameId) {
    const ribbon = document.getElementById(`ribbon-${gameId}`);
    const full = document.getElementById(`full-${gameId}`);
    if (ribbon && full) {
        ribbon.classList.toggle('d-none');
        full.classList.toggle('d-none');
    }
};

// ==========================================
// DYNAMIC WEATHER THEME GENERATOR
// ==========================================
function getWeatherTheme(isDome, wSpeed, wPrecip) {
    if (isDome) {
        // Controlled indoor climate: Crisp, silver/grey
        return {
            bg: 'background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);',
            text: 'text-dark',
            border: 'border-secondary'
        };
    } else if (wPrecip > 0) {
        // Rain/Snow: Stormy, dark greys
        return {
            bg: 'background: linear-gradient(135deg, #64748b 0%, #334155 100%);',
            text: 'text-white',
            border: 'border-dark',
            muted: 'text-light'
        };
    } else if (wSpeed >= 15) {
        // High Winds: Flowing blues
        return {
            bg: 'background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);',
            text: 'text-dark',
            border: 'border-info'
        };
    } else {
        // Standard Clear Day: Clean white
        return {
            bg: 'background: #ffffff;',
            text: 'text-dark',
            border: 'border-dark'
        };
    }
}

// ==========================================
// HTML GENERATORS
// ==========================================
function getRibbonHtml(game, gameId) {
    const wSpeed = game.weather.windSpeed || 0;
    const wPrecip = game.weather.precip || 0;
    const isDome = game.stadium && game.stadium.roof === "Dome";
    
    const theme = getWeatherTheme(isDome, wSpeed, wPrecip);
    const mutedClass = theme.muted || 'text-muted';
    
    let weatherSnippet = isDome ? "🏟️ Dome" : `🌡️ ${game.weather.temp}° 💨 ${wSpeed}mph`;
    if (wPrecip > 0) weatherSnippet += ` 🌧️ ${wPrecip}"`;

    return `
    <div class="row g-0 align-items-center py-2 px-2 ${theme.border} rounded shadow-sm" style="${theme.bg} cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.01)'" onmouseout="this.style.transform='scale(1)'" onclick="toggleSingleCard('${gameId}')">
        <div class="col-3 text-start border-end pe-2">
            <span class="badge bg-dark mb-1" style="font-size: 0.65rem;">${game.status}</span><br>
            <span class="${mutedClass} fw-bold" style="font-size: 0.70rem;">${weatherSnippet}</span>
        </div>
        <div class="col-9 ps-3">
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="text-truncate fw-bold ${theme.text}" style="font-size: 0.85rem;">${game.away_team}</span>
            </div>
            <div class="d-flex justify-content-between align-items-center">
                <span class="text-truncate fw-bold ${theme.text}" style="font-size: 0.85rem;">@ ${game.home_team}</span>
            </div>
        </div>
    </div>`;
}

function getFullHtml(game, gameId) {
    let impactText = "✅ Clear Conditions";
    let impactAlertClass = "border-success bg-light text-dark";
    
    const wSpeed = game.weather.windSpeed || 0;
    const wPrecip = game.weather.precip || 0;
    const isDome = game.stadium && game.stadium.roof === "Dome";
    
    const theme = getWeatherTheme(isDome, wSpeed, wPrecip);
    const mutedClass = theme.muted || 'text-muted';
    
    if (isDome) {
        impactText = "🏟️ Dome Environment (Perfect Conditions)";
        impactAlertClass = "border-secondary bg-white text-dark";
    } else {
        if (wSpeed >= 15 && wPrecip > 0) {
            impactText = "🚨 Heavy Weather: Passing/kicking downgraded, boost RBs.";
            impactAlertClass = "border-danger bg-dark text-white";
        } else if (wSpeed >= 15) {
            impactText = "💨 High Winds: Deep passing & kicking downgraded.";
            impactAlertClass = "border-info bg-white text-dark";
        } else if (wPrecip > 0) {
            impactText = "🌧️ Wet Conditions: Potential for sloppy play & turnovers.";
            impactAlertClass = "border-primary bg-dark text-white";
        }
    }
    
    const surfaceText = game.stadium ? game.stadium.surface : "Unknown";
    const stadiumName = game.stadium ? game.stadium.name : "TBD Location";

    return `
    <div class="card shadow-sm p-3 ${theme.border} h-100" style="${theme.bg} cursor: pointer; transition: transform 0.2s;" onclick="toggleSingleCard('${gameId}')" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
        <div class="d-flex justify-content-between align-items-start mb-2">
            <h6 class="fw-bold ${theme.text} mb-0">${game.game_info}</h6>
            <span class="badge bg-dark">${game.status}</span>
        </div>
        <p class="${mutedClass} mb-2" style="font-size: 0.85rem;">📍 ${stadiumName} | 🌱 ${surfaceText}</p>
        <hr class="mt-1 mb-2 border-secondary">
        <div class="d-flex justify-content-between mb-3 fw-bold ${theme.text} px-2">
            <span>🌡️ ${game.weather.temp}°F</span>
            <span>💨 ${wSpeed} mph</span>
            <span>🌧️ ${wPrecip}"</span>
        </div>
        <div class="mt-auto p-2 border-start border-3 ${impactAlertClass} text-sm fw-bold shadow-sm">
            ${impactText}
        </div>
    </div>`;
}

// ==========================================
// MAIN RENDER LOOP
// ==========================================
function renderGames(gamesArray, container) {
    container.innerHTML = ''; 
    
    if (gamesArray.length === 0) {
        container.innerHTML = '<div class="alert alert-light border">No active matchups right now.</div>';
        return;
    }
    
    gamesArray.forEach(([gameId, game]) => {
        const cardWrapper = document.createElement('div');
        cardWrapper.className = "col-md-6 col-lg-4 mb-3";
        
        // Setup classes based on global state
        const ribbonClass = globalScoreboardMode ? 'd-none' : '';
        const fullClass = globalScoreboardMode ? '' : 'd-none';

        cardWrapper.innerHTML = `
            <div id="card-${gameId}" class="position-relative h-100">
                <div class="ribbon-view ${ribbonClass}" id="ribbon-${gameId}">
                    ${getRibbonHtml(game, gameId)}
                </div>
                <div class="full-view ${fullClass}" id="full-${gameId}">
                    ${getFullHtml(game, gameId)}
                </div>
            </div>
        `;
        container.appendChild(cardWrapper);
    });
}
