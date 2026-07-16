// ==========================================
// STATE MANAGEMENT & FIREBASE (MLB STYLE)
// ==========================================
let savedScoreboardState = localStorage.getItem('nflScoreboardMode');
let globalScoreboardMode = savedScoreboardState !== null ? savedScoreboardState === 'true' : false; 

window.HAS_SHOWN_TUTORIAL = false;
let allGamesData = {};
let currentSelectedWeek = null;
let availableWeeks = [];

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
        allGamesData = snapshot.val() || {};
        
        // Extract unique weeks based on the 'week_order' assigned by Python
        const weeksMap = new Map();
        Object.values(allGamesData).forEach(g => {
            if (g.week_label) weeksMap.set(g.week_label, g.week_order);
        });
        
        // Sort weeks chronologically
        availableWeeks = Array.from(weeksMap.entries()).sort((a,b) => a[1] - b[1]).map(e => e[0]);
        
        // Default to the first available week if not set
        if (availableWeeks.length > 0 && (!currentSelectedWeek || !availableWeeks.includes(currentSelectedWeek))) {
            currentSelectedWeek = availableWeeks[0];
        }

        updateUI();
    });

    const radarModal = document.getElementById('radarModal');
    if (radarModal) {
        radarModal.addEventListener('hidden.bs.modal', () => {
            const iframe = document.getElementById('radarFrame');
            if (iframe) iframe.src = ''; 
        });
    }
});

// ==========================================
// RENDER & FILTER CONTROLS
// ==========================================
function updateUI() {
    const mainContainer = document.getElementById('games-container');
    const singleTeamContainer = document.getElementById('team-weather-container');
    
    let filteredGames = Object.entries(allGamesData);

    // If we are on the main hub, filter by the selected week
    if (mainContainer) {
        filteredGames = filteredGames.filter(([id, g]) => g.week_label === currentSelectedWeek);
        renderGames(filteredGames, mainContainer, false);
    } else if (singleTeamContainer) {
        // If we are on a single team page, show both weeks for that specific team
        const targetTeamId = window.TARGET_TEAM_ID;
        filteredGames = filteredGames.filter(([id, g]) => g.home_id === targetTeamId || g.away_id === targetTeamId);
        
        // Sort them chronologically by week_order
        filteredGames.sort((a, b) => (a[1].week_order || 0) - (b[1].week_order || 0));
        
        renderGames(filteredGames, singleTeamContainer, true);
    }
}

// --- NEW HELPER: Toggle between current and next week ---
window.toggleWeek = function() {
    if (window.dismissTutorials) window.dismissTutorials();
    if (availableWeeks.length > 1) {
        if (currentSelectedWeek === availableWeeks[0]) {
            currentSelectedWeek = availableWeeks[1];
        } else {
            currentSelectedWeek = availableWeeks[0];
        }
        updateUI();
    }
};

window.toggleSingleCard = function(e, gameId) {
    if (e && e.target.closest('a, button, input, label, [data-bs-toggle="collapse"], select')) return; 
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

window.showRadar = function(url, venueName) {
    const modalElement = document.getElementById('radarModal');
    const modalTitle = document.querySelector('#radarModal .modal-title');
    const iframe = document.getElementById('radarFrame');
    
    if(modalTitle) modalTitle.innerText = `Radar: ${venueName}`;

    const myModal = bootstrap.Modal.getOrCreateInstance(modalElement);
    if(iframe) iframe.src = '';

    const loadMap = function () {
        if(iframe) iframe.src = url; 
        modalElement.removeEventListener('shown.bs.modal', loadMap); 
    };

    modalElement.addEventListener('shown.bs.modal', loadMap);
    myModal.show();
}

function getShortTeamName(fullName) {
    if (!fullName || fullName === "TBD") return "TBD";
    const parts = fullName.split(" ");
    return parts[parts.length - 1]; 
}

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

// ==========================================
// COMPONENT RENDERERS
// ==========================================
function createGameCard(gameId, game, isSingleTeam) {
    const isDome = game.stadium && (game.stadium.roof === "Dome" || game.stadium.roof === "Retractable");
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

    let badgeText = "TBD";
    let badgeStyle = "bg-light text-dark border";

    if (game.status === 'pre' && game.game_time) {
        const d = new Date(game.game_time);
        const day = d.toLocaleDateString('en-US', { weekday: 'short' }); 
        const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        badgeText = `${day} ${time}`; 
    } else if (game.status === 'in') {
        badgeText = game.clock || 'LIVE';
        badgeStyle = "bg-danger text-white border-danger";
    } else if (game.status === 'post') {
        badgeText = "FINAL";
        badgeStyle = "bg-secondary text-white border-secondary";
    } else {
        badgeText = game.status ? game.status.toUpperCase() : "TBD";
    }

    const awayShortName = getShortTeamName(game.away_team);
    const homeShortName = getShortTeamName(game.home_team);

    const awayLogo = `https://a.espncdn.com/i/teamlogos/nfl/500/${game.away_id.toLowerCase()}.png`;
    const homeLogo = `https://a.espncdn.com/i/teamlogos/nfl/500/${game.home_id.toLowerCase()}.png`;

    const weatherEmojiLine = isDome ? `Roof Closed 🌡️${w.temp}°` : `🌧️${w.precip}" 🌡️${w.temp}° 💨${w.windSpeed}mph`;
    const showRibbon = globalScoreboardMode ? 'block' : 'none';
    const showFull = globalScoreboardMode ? 'none' : 'block';
    
    let displayRain = isDome ? "0%" : `${w.precip}"`;
    let windArrow = "💨";
    let windCss = "bg-secondary text-white";
    
    // Dynamic naming handling neutral location data from backend updates
    const stadiumName = game.stadium ? game.stadium.name : "TBD Location";
    const stadiumLocation = game.stadium && game.stadium.city && game.stadium.state 
        ? `${game.stadium.city}, ${game.stadium.state}` 
        : "";
    const displayStadiumInfo = stadiumLocation ? `${stadiumName} (${stadiumLocation})` : stadiumName;

    const stadiumLat = game.stadium ? game.stadium.lat : 39.0;
    const stadiumLon = game.stadium ? game.stadium.lon : -95.0;
    
    const radarUrl = `https://embed.windy.com/embed2.html?lat=${stadiumLat}&lon=${stadiumLon}&detailLat=${stadiumLat}&detailLon=${stadiumLon}&width=650&height=450&zoom=11&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=mph&metricTemp=%C2%B0F&radarRange=-1`;

    let hourlyHtml = '';
    if (isDome) {
        hourlyHtml = `<div class="text-center mt-2"><small class="text-muted">Indoor Conditions Controlled</small></div>`;
    } else if (w.hourly && w.hourly.length > 0) {
        const hoursMarkup = w.hourly.map((h) => {
            const dateObj = h.timestamp ? new Date(h.timestamp) : new Date();
            if(!h.timestamp) dateObj.setHours(h.hour || 12, 0, 0, 0); 

            const hr12 = dateObj.getHours() % 12 || 12;
            const ampm = dateObj.getHours() >= 12 ? 'PM' : 'AM';
            let icon = '☀️';
            
            const isNight = dateObj.getHours() >= 20 || dateObj.getHours() < 6;
            if (h.precipChance >= 30) {
                icon = h.isThunderstorm ? '⛈️' : (h.isSnow ? '🌨️' : '🌧️');
            } else if (h.precipChance > 0) {
                icon = '⛅';
            } else if (isNight) {
                icon = '🌙';
            }

            return `
                <div class="hour-card">
                    <div class="hour-time">${hr12}${ampm}</div>
                    <div class="hour-icon">${icon}</div>
                    <div class="hour-pop">${h.precipChance >= 20 ? h.precipChance + '%' : '&nbsp;'}</div>
                    <div class="hour-temp">${h.temp !== undefined ? h.temp + '°' : '--'}</div>
                </div>`;
        }).join('');
        hourlyHtml = `<div class="hourly-scroll-container">${hoursMarkup}</div>`;
    }

    const singleTeamWeekLabel = isSingleTeam && game.week_label ? 
        `<div class="text-center bg-dark text-white fw-bold py-1 w-100" style="font-size: 0.7rem; letter-spacing: 1px; text-transform: uppercase;">${game.week_label}</div>` : '';

    const card = document.createElement('div');
    card.className = isSingleTeam ? 'w-100 animate-card mb-2 px-1' : 'col-md-6 col-lg-4 col-xl-3 animate-card mb-2 px-1';
    card.id = `game-${gameId}`;
    
    card.innerHTML = `
        <div class="card game-card shadow-sm ${borderClass} ${bgClass}" style="overflow: hidden;">
            ${singleTeamWeekLabel}
            <div class="ribbon-view p-2 position-relative" onclick="toggleSingleCard(event, '${gameId}')" style="cursor: pointer; display: ${showRibbon};">
                <div class="d-flex align-items-center mb-1">
                    <span class="badge ${badgeStyle} flex-shrink-0 px-2 py-1" style="font-size: 0.65rem;">${badgeText}</span>
                    <div class="fw-bold text-dark text-center flex-grow-1 ms-2" style="font-size: 0.75rem; letter-spacing: 0.2px;">
                        ${weatherEmojiLine}
                    </div>
                </div>
                <div class="d-flex align-items-center mt-1" style="gap: 4px;">
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="${awayLogo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">${awayShortName}</span>
                    </div>
                    <span class="fw-bold text-muted flex-shrink-0 lh-1" style="font-size: 0.7rem;">@</span>
                    <div class="d-flex align-items-center flex-shrink-0" style="gap: 3px;">
                        <img src="${homeLogo}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.style.display='none'">
                        <span class="fw-bold text-dark lh-1" style="font-size: 0.75rem;">${homeShortName}</span>
                    </div>
                    <div class="text-truncate text-end fw-bold flex-grow-1 ms-1" style="font-size: 0.7rem; opacity: 0.75;">${displayStadiumInfo}</div>
                </div>
            </div>

            <div class="full-card-view" onclick="toggleSingleCard(event, '${gameId}')" style="cursor: pointer; display: ${showFull};">
                <div class="card-body px-2 pt-2 pb-2"> 
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge ${badgeStyle}">${badgeText}</span>
                        <span class="stadium-name text-truncate text-end flex-grow-1 ms-2" style="font-size: 0.8rem; font-weight: 600;">${displayStadiumInfo}</span>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center px-1 mb-1">
                        <div class="d-flex align-items-center text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="${awayLogo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain; filter: drop-shadow(0px 1px 1px rgba(0,0,0,0.1));" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate" style="font-size: 0.95rem;">${awayShortName}</div>
                        </div>
                        <div class="text-center text-muted fw-bold" style="width: 10%; font-size: 0.8rem;">@</div>
                        <div class="d-flex align-items-center justify-content-end text-truncate" style="width: 45%; min-width: 0;"> 
                            <img src="${homeLogo}" class="me-2" style="width: 24px; height: 24px; object-fit: contain; filter: drop-shadow(0px 1px 1px rgba(0,0,0,0.1));" onerror="this.style.display='none'">
                            <div class="fw-bold lh-sm text-dark text-truncate text-end" style="font-size: 0.95rem;">${homeShortName}</div>
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
                    
                    ${hourlyHtml}
                    
                    <div class="mt-2 mb-2">
                        <button class="btn btn-sm btn-outline-primary w-100 py-1 fw-bold" style="font-size: 0.8rem;" onclick="showRadar('${radarUrl}', '${stadiumName}')">
                            🗺️ View Live Radar Map
                        </button>
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
    
    // Inject the Header, Week Toggle Button, and Expand Button ONLY for the main grid
    if (!isSingleTeam && gamesArray.length > 0) {
        
        let expandTutorialHtml = '';
        if (!window.HAS_SHOWN_TUTORIAL) {
            expandTutorialHtml = `<div class="tutorial-tooltip text-primary fw-bold mb-1" style="font-size: 0.75rem; animation: tutorialBounce 1.5s infinite;">👇 Click to expand all cards</div>`;
        }
        
        let weekBtnText = currentSelectedWeek === availableWeeks[0] ? 'Next Week ➡️' : '⬅️ Last Week';
        let weekBtnDisplay = availableWeeks.length > 1 ? 'inline-block' : 'none'; 

        const controlRow = document.createElement('div');
        controlRow.className = 'col-12 mb-3 mt-1 position-relative d-flex flex-column align-items-center';
        controlRow.innerHTML = `
            <div class="fw-bold text-secondary mb-2" style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">
                📅 ${currentSelectedWeek}
            </div>
            ${expandTutorialHtml}
            <div class="d-flex justify-content-center gap-2">
                <button class="btn btn-sm shadow-sm fw-bold px-3 py-1 border border-primary text-primary" style="background-color: #f8f9fa; border-radius: 20px; display: ${weekBtnDisplay};" onclick="window.toggleWeek()">
                    ${weekBtnText}
                </button>
                <button class="btn btn-sm shadow-sm fw-bold px-4 py-1 border border-secondary" style="background-color: #fff; color: #495057; border-radius: 20px;" onclick="window.toggleAllWeatherCards()">
                    <span id="expand-toggle-icon">${globalScoreboardMode ? '▼' : '▲'}</span> 
                    <span id="expand-toggle-text">${globalScoreboardMode ? 'Expand All Cards' : 'Collapse All Cards'}</span>
                </button>
            </div>
        `;
        container.appendChild(controlRow);
        
        setTimeout(window.dismissTutorials, 8000);
    }
    
    const row = document.createElement('div');
    row.className = 'row w-100 m-0 p-0 align-items-start';
    
    gamesArray.forEach(([gameId, game]) => {
        row.appendChild(createGameCard(gameId, game, isSingleTeam));
    });
    
    container.appendChild(row);
}
