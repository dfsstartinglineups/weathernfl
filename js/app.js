// ==========================================
// STATE MANAGEMENT & FIREBASE (MLB STYLE)
// ==========================================
let savedScoreboardState = localStorage.getItem('nflScoreboardMode');
// Default to false (Expanded View) for desktop, just like the MLB site
let globalScoreboardMode = savedScoreboardState !== null ? savedScoreboardState === 'true' : false; 

window.HAS_SHOWN_TUTORIAL = false;

const nflStyle = document.createElement('style');
nflStyle.innerHTML = `
    @keyframes tutorialBounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    .tutorial-tooltip {
        transition: opacity 0.4s ease-out;
        pointer-events: none; 
    }
`;
document.head.appendChild(nflStyle);

window.dismissTutorials = function() {
    window.HAS_SHOWN_TUTORIAL = true;
    document.querySelectorAll('.tutorial-tooltip').forEach(el => {
        el.style.opacity = '0'; 
        setTimeout(() => el.remove(), 400); 
    });
};

document.addEventListener('DOMContentLoaded', () => {
    console.log("🏈 Initializing NFL Weather App (MLB Theme)...");

    const firebaseConfig = { databaseURL: "https://nbastartingfive-8b420-default-rtdb.firebaseio.com/" };
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    
    const db = firebase.database();
    db.ref('nfl_weather').on('value', (snapshot) => {
        const data = snapshot.val();
        const mainContainer = document.getElementById('games-container');
        const singleTeamContainer = document.getElementById('team-weather-container');
        
        if(data) {
            if(singleTeamContainer) {
                const targetTeamId = window.TARGET_TEAM_ID;
                const filtered = Object.entries(data).filter(([id, g]) => g.home_id === targetTeamId || g.away_id === targetTeamId);
                renderGames(filtered, singleTeamContainer, true);
            } else if(mainContainer) {
                renderGames(Object.entries(data), mainContainer, false);
            }
        } else {
            const noDataHtml = '<div class="col-12 text-center text-muted">No game data currently available.</div>';
            if (singleTeamContainer) singleTeamContainer.innerHTML = noDataHtml;
            if (mainContainer) mainContainer.innerHTML = noDataHtml;
        }
    });
});

// ==========================================
// CARD TOGGLING & TUTORIAL LOGIC
// ==========================================
window.toggleSingleCard = function(e, gameId) {
    if (e && e.target.closest('a, button, input, label, [data-bs-toggle="collapse"]')) return; 
    if (window.dismissTutorials) window.dismissTutorials();
    
    const card = document.getElementById(`game-${gameId}`);
    if (!card) return;
    
    const ribbon = card.querySelector('.ribbon-view');
    const full = card.querySelector('.full-card-view');
    
    if (ribbon.style.display === 'none') {
        ribbon.style.display = 'block';
        full.style.display = 'none';
    } else {
        ribbon.style.display = 'none';
        full.style.display = 'block';
    }
};

window.toggleAllWeatherCards = function() {
    if (window.dismissTutorials) window.dismissTutorials();
    globalScoreboardMode = !globalScoreboardMode;
    localStorage.setItem('nflScoreboardMode', globalScoreboardMode);
    
    const btnText = document.getElementById('expand-toggle-text');
    const btnIcon = document.getElementById('expand-toggle-icon');
    if (btnText && btnIcon) {
        btnText.innerText = globalScoreboardMode ? 'Expand All Cards' : 'Collapse All Cards';
        btnIcon.innerText = globalScoreboardMode ? '▼' : '▲';
    }
    
    document.querySelectorAll('.game-card').forEach(card => {
        const ribbon = card.querySelector('.ribbon-view');
        const full = card.querySelector('.full-card-view');
        if (ribbon && full) {
            ribbon.style.display = globalScoreboardMode ? 'block' : 'none';
            full.style.display = globalScoreboardMode ? 'none' : 'block';
        }
    });
};

function generateMatchupAnalysis(weather, isDome) {
    if (isDome) return "✅ <b>Dome Environment:</b> Controlled climate with zero weather impact. Perfect passing conditions.";
    
    let notes = [];
    if (weather.windSpeed >= 15 && weather.precip > 0) {
        notes.push("🚨 <b>Heavy Weather:</b> Passing and kicking severely downgraded. Expect a run-heavy script.");
    } else if (weather.windSpeed >= 15) {
        notes.push("💨 <b>High Winds:</b> Deep passing and long field goals downgraded.");
    } else if (weather.precip > 0) {
        notes.push("🌧️ <b>Wet Conditions:</b> Potential for sloppy play, fumbles, and dropped passes.");
    }
    
    if (weather.temp >= 85) notes.push("🔥 <b>Heat Alert:</b> High temperatures could lead to player fatigue late in the game.");
    if (weather.temp <= 32) notes.push("❄️ <b>Freezing:</b> Cold weather typically favors the ground game and lowers total scoring.");
    
    if (notes.length === 0) return "✅ <b>Neutral:</b> Fair weather conditions. No significant weather impact.";
    return notes.join("<br>");
}

function createGameCard(gameId, game, isSingleTeam) {
    const isDome = game.stadium && game.stadium.roof === "Dome";
    const w = game.weather || { temp: 72, windSpeed: 0, precip: 0 };
    
    let borderClass = ""; 
    let bgClass = "bg-weather-sunny";
    if (isDome) {
        bgClass = "bg-weather-roof";
    } else if (w.precip > 0.5) {
        borderClass = "border-danger border-3";
        bgClass = "bg-weather-storm";
    } else if (w.precip > 0) {
        borderClass = "border-warning border-3";
        bgClass = "bg-weather-rain";
    } else if (w.windSpeed >= 15) {
        bgClass = "bg-weather-cloudy";
    }

    // Using ESPN's NFL logo endpoints
    const awayLogo = `https://a.espncdn.com/i/teamlogos/nfl/500/${game.away_id.toLowerCase()}.png`;
    const homeLogo = `https://a.espncdn.com/i/teamlogos/nfl/500/${game.home_id.toLowerCase()}.png`;

    const weatherEmojiLine = isDome ? `Roof Closed 🌡️${w.temp}°` : `🌧️${w.precip}" 🌡️${w.temp}° 💨${w.windSpeed}mph`;
    
    const showRibbon = globalScoreboardMode ? 'block' : 'none';
    const showFull = globalScoreboardMode ? 'none' : 'block';
    
    let displayRain = isDome ? "0%" : `${w.precip}"`;
    let windArrow = "💨";
    let windCss = "bg-secondary text-white";
    
    const card = document.createElement('div');
    card.className = isSingleTeam ? 'w-100 animate-card mb-2 px-1' : 'col-md-6 col-lg-4 col-xl-3 animate-card mb-2 px-1';
    card.id = `game-${gameId}`;
    
    card.innerHTML = `
        <div class="card game-card shadow-sm ${borderClass} ${bgClass}" style="overflow: hidden;">
            
            <div class="ribbon-view p-2 position-relative" onclick="toggleSingleCard(event, '${gameId}')" style="cursor: pointer; display: ${showRibbon};">
                <div class="d-flex align-items-center mb-1">
                    <span class="badge bg-light text-dark border flex-shrink-0 px-2 py-1" style="font-size: 0.65rem;">${game.status}</span>
                    <div class="fw-bold text-dark text-center flex-grow-1 ms-2" style="font-size: 0.75rem; letter-spacing: 0.2px;">
                        ${weatherEmojiLine}
                    </div>
                </div>
                <div class="d-flex align-items-center mt-1" style="gap: 4px;">
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="${awayLogo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">${game.away_id}</span>
                    </div>
                    <span class="fw-bold text-muted flex-shrink-0 lh-1" style="font-size: 0.7rem;">@</span>
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="${homeLogo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">${game.home_id}</span>
                    </div>
                    <div class="text-truncate text-end fw-bold flex-grow-1 ms-1" style="font-size: 0.7rem; opacity: 0.75;">${game.stadium?.name || 'TBD'}</div>
                </div>
            </div>

            <div class="full-card-view" onclick="toggleSingleCard(event, '${gameId}')" style="cursor: pointer; display: ${showFull};">
                <div class="card-body px-2 pt-2 pb-2"> 
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-light text-dark border">${game.status}</span>
                        <span class="stadium-name text-truncate text-end flex-grow-1 ms-2" style="font-size: 0.8rem; font-weight: 600;">${game.stadium?.name || 'TBD'}</span>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center px-1 mb-1">
                        <div class="d-flex align-items-center text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="${awayLogo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain; filter: drop-shadow(0px 1px 1px rgba(0,0,0,0.1));" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate" style="font-size: 0.95rem;">${game.away_team}</div>
                        </div>
                        <div class="text-center text-muted fw-bold" style="width: 10%; font-size: 0.8rem;">@</div>
                        <div class="d-flex align-items-center justify-content-end text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="${homeLogo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain; filter: drop-shadow(0px 1px 1px rgba(0,0,0,0.1));" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate text-end" style="font-size: 0.95rem;">${game.home_team}</div>
                        </div>
                    </div>
                    
                    <div class="weather-row row text-center align-items-center mt-2 mx-0">
                        <div class="col-3 border-end px-1">
                            <div class="fw-bold">${w.temp}°F</div>
                            <div class="small text-muted" style="font-size: 0.7rem;">Temp</div>
                        </div>
                        <div class="col-3 border-end px-1">
                            <div class="fw-bold text-dark">🌱</div>
                            <div class="small text-muted" style="font-size: 0.7rem;">${game.stadium?.surface || '-'}</div>
                        </div>
                        <div class="col-3 border-end px-1">
                            <div class="fw-bold text-primary" style="white-space: nowrap;">${displayRain}</div>
                            <div class="small text-muted" style="font-size: 0.7rem;">Rain</div>
                        </div>
                        <div class="col-3 px-1">
                            <div class="fw-bold">${w.windSpeed} <span style="font-size:0.7em">mph</span></div>
                            <span class="wind-badge ${windCss}" style="font-size: 0.55rem; white-space: nowrap; display: inline-block; padding: 2px 4px;">${windArrow}</span>
                        </div>
                    </div>
                    
                    <div class="analysis-box">
                        <span class="analysis-title">✨ Weather Impact</span>
                        ${generateMatchupAnalysis(w, isDome)}
                    </div>
                </div>
            </div>
        </div>
    `;
    return card;
}

function renderGames(gamesArray, container, isSingleTeam) {
    container.innerHTML = ''; 
    
    if (gamesArray.length === 0) {
        container.innerHTML = '<div class="alert alert-light border">No active matchups right now.</div>';
        return;
    }
    
    const row = document.createElement('div');
    row.className = 'row w-100 m-0 p-0 align-items-start';
    
    gamesArray.forEach(([gameId, game]) => {
        row.appendChild(createGameCard(gameId, game, isSingleTeam));
    });
    
    if (!isSingleTeam && gamesArray.length > 0) {
        let expandTutorialHtml = '';
        if (!window.HAS_SHOWN_TUTORIAL) {
            expandTutorialHtml = `<div class="tutorial-tooltip text-primary fw-bold mb-1" style="font-size: 0.75rem; animation: tutorialBounce 1.5s infinite;">👇 Click to expand all cards</div>`;
        }

        const toggleRow = document.createElement('div');
        toggleRow.className = 'col-12 text-center mb-3 mt-1 position-relative';
        toggleRow.innerHTML = `
            ${expandTutorialHtml}
            <button class="btn btn-sm shadow-sm fw-bold px-4 py-1" style="background-color: #fff; border: 1px solid #dee2e6; color: #495057; border-radius: 20px;" onclick="window.toggleAllWeatherCards()">
                <span id="expand-toggle-icon">${globalScoreboardMode ? '▼' : '▲'}</span> 
                <span id="expand-toggle-text">${globalScoreboardMode ? 'Expand All Cards' : 'Collapse All Cards'}</span>
            </button>
        `;
        container.appendChild(toggleRow);
        
        setTimeout(window.dismissTutorials, 8000);
    }
    
    container.appendChild(row);
}
