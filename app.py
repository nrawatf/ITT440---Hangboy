from flask import Flask, render_template_string, request, jsonify, session
import random
import threading

app = Flask(__name__)
app.secret_key = "itt440_secret_hangboy_key"

state_lock = threading.Lock()

# 🎯 Your Official Tournament Match Progression Pools
words_pool = [
    {"word": "CHALLENGE", "hint": "A task or situation that tests someone's abilities."},
    {"word": "JOURNEY", "hint": "An act of traveling from one place to another."},
    {"word": "HORIZON", "hint": "The line at which the earth's surface and the sky appear to meet."},
    {"word": "MYSTERY", "hint": "Something that is difficult or impossible to understand or explain."},
    {"word": "VICTORY", "hint": "An act of defeating an enemy or opponent."}
]

# Shared Global State Engine (Mirrors your precise dict architecture)
players_directory = {}  # session_id -> assigned name
scores = {}             # name -> [lvl1, lvl2, lvl3, lvl4, lvl5]
game_state = {
    "current_level": 0,
    "secret_word": "",
    "hint": "",
    "revealed_word": [],
    "global_lives": 6,
    "is_game_over": False,
    "system_logs": ["🏆 TOURNAMENT LOBBY ACTIVE. Synchronizing sessions..."]
}

def load_level():
    lvl = game_state["current_level"]
    if lvl < len(words_pool):
        current = words_pool[lvl]
        game_state["secret_word"] = current["word"]
        game_state["hint"] = current["hint"]
        game_state["revealed_word"] = ["_" for _ in current["word"]]
        game_state["global_lives"] = 6
        game_state["is_game_over"] = False

# Initialize Level 1 parameters on server startup
load_level()

def get_rankings_array():
    """Generates the competitive matrix breakdown matching your scoreboard tracking."""
    player_summaries = []
    for name, lvl_points in scores.items():
        player_summaries.append({
            "name": name,
            "total": sum(lvl_points),
            "lvls": lvl_points
        })
    player_summaries.sort(key=lambda x: x["total"], reverse=True)
    return player_summaries

# --- High-Contrast Cyberpunk UI Layout (Merged Auth & Dashboard Panels) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Multiplayer Hangboy Player Station</title>
    <style>
        body { background-color: #1E1E2E; color: #F8F8F2; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
        .auth-container { max-width: 500px; margin: 80px auto; background: #252538; padding: 40px; border-radius: 8px; border: 2px solid #FF007F; box-shadow: 0 0 15px rgba(255,0,127,0.2); }
        .main-container { max-width: 950px; margin: 10px auto; display: none; }
        .top-bar { background: #252538; padding: 12px 20px; border-radius: 4px; display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem; margin-bottom: 15px; }
        .flex-split { display: flex; gap: 20px; justify-content: center; }
        .canvas-panel { background: #11111B; border: 2px solid #FF007F; padding: 15px; width: 240px; height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .controls-panel { background: transparent; flex-grow: 1; display: flex; flex-direction: column; gap: 12px; }
        .card { background: #11111B; border: 1px solid #252538; padding: 12px; text-align: left; border-radius: 4px; }
        .word-card { background: #252538; padding: 20px; text-align: center; border-radius: 4px; }
        .word-lbl { font-family: 'Consolas', 'Courier New', monospace; font-size: 2.5rem; font-weight: bold; color: #FFFF00; letter-spacing: 6px; }
        .input-bar { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 10px; }
        input.text-field { font-family: 'Consolas', monospace; font-size: 1.3rem; background: #11111B; border: 1px solid #A4A4C1; color: #FFFF00; text-align: center; padding: 6px; border-radius: 4px; }
        button.action-btn { font-family: inherit; font-weight: bold; font-size: 1rem; padding: 8px 20px; border: none; cursor: pointer; border-radius: 4px; }
        .btn-join { background: #00F5D4; color: #1E1E2E; width: 100%; padding: 12px; font-size: 1.1rem; }
        .btn-submit { background: #00F5D4; color: #1E1E2E; }
        .btn-next { background: #FF007F; color: white; display: none; }
        .log-box { background: #11111B; border: 1px solid #A4A4C1; font-family: 'Consolas', monospace; font-size: 0.85rem; color: #A4A4C1; padding: 10px; text-align: left; height: 100px; overflow-y: auto; margin-top: 15px; border-radius: 4px; }
        .leaderboard-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(17,17,27,0.95); z-index: 100; align-items: center; justify-content: center; }
        .leaderboard-modal { background: #11111B; border: 2px solid #FF007F; padding: 30px; border-radius: 8px; width: 80%; max-width: 700px; }
        .tree-table { width: 100%; border-collapse: collapse; margin-top: 15px; color: #F8F8F2; }
        .tree-table th, .tree-table td { background: #252538; border: 1px solid #1E1E2E; padding: 10px; text-align: center; }
        .tree-table th { background: #1E1E2E; color: #00F5D4; }
    </style>
    <script>
        let isRegistered = false;
        let lastLevel = 0;

        // Dynamic Vector Execution Context (Replaces your canvas drawing function)
        function renderVectorGraphics(lives) {
            const canvas = document.getElementById('hangman-vector');
            if(!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = "#inner";
            
            // Base Structure
            ctx.strokeStyle = "#F8F8F2"; ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(20, 250); ctx.lineTo(180, 250); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(60, 250); ctx.lineTo(60, 40); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(60, 40); ctx.lineTo(140, 40); ctx.stroke();
            ctx.lineWidth = 2;
            ctx.beginPath(); ctx.moveTo(140, 40); ctx.lineTo(140, 70); ctx.stroke();

            ctx.strokeStyle = "#00F5D4"; ctx.lineWidth = 3;
            if(lives <= 5) { ctx.beginPath(); ctx.arc(140, 90, 20, 0, Math.PI*2); ctx.stroke(); }
            if(lives <= 4) { ctx.beginPath(); ctx.moveTo(140, 110); ctx.lineTo(140, 180); ctx.stroke(); }
            if(lives <= 3) { ctx.beginPath(); ctx.moveTo(140, 130); ctx.lineTo(110, 150); ctx.stroke(); }
            if(lives <= 2) { ctx.beginPath(); ctx.moveTo(140, 130); ctx.lineTo(170, 150); ctx.stroke(); }
            if(lives <= 1) { ctx.beginPath(); ctx.moveTo(140, 180); ctx.lineTo(110, 220); ctx.stroke(); }
            if(lives <= 0) { 
                ctx.strokeStyle = "#FF477E";
                ctx.beginPath(); ctx.moveTo(140, 180); ctx.lineTo(170, 220); ctx.stroke(); 
                ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(132, 85); ctx.lineTo(138, 91); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(138, 85); ctx.lineTo(132, 91); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(142, 85); ctx.lineTo(148, 91); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(148, 85); ctx.lineTo(142, 91); ctx.stroke();
            }
        }

        async function registerUser() {
            let nickInput = document.getElementById('nickname-input').value.trim().toUpperCase();
            if(!nickInput) { alert("Nickname entry cannot be empty!"); return; }
            
            let res = await fetch('/join', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: nickInput })
            });
            let data = await res.json();
            if(data.success) {
                isRegistered = true;
                document.getElementById('auth-panel').style.display = 'none';
                document.getElementById('dashboard-panel').style.display = 'block';
                document.getElementById('player-lbl').innerText = "👤 Player: " + nickInput;
                document.getElementById('guess-input').focus();
            }
        }

        // State Broker Polling Engine (Synchronizes matches every 750ms)
        setInterval(async () => {
            if(!isRegistered) return;
            let response = await fetch('/state');
            let data = await response.json();
            
            document.getElementById('word-lbl').innerText = data.revealed_word;
            document.getElementById('hint-txt').innerText = data.hint;
            document.getElementById('level-lbl').innerText = "Level: " + (data.current_level + 1) + "/5";
            document.getElementById('lives-lbl').innerText = "❤️ Lives: " + data.global_lives + "/6";
            
            renderVectorGraphics(data.global_lives);

            // Rebuild Streaming Log Lines
            let logsContainer = document.getElementById('logs-stream');
            logsContainer.innerHTML = data.system_logs.map(log => ">> " + log).join("<br>");
            logsContainer.scrollTop = logsContainer.scrollHeight;

            // Manage Phase Advancement Controllers
            if(!data.revealed_word.includes('_') && data.current_level < 4) {
                document.getElementById('next-btn').style.display = 'inline-block';
            } else {
                document.getElementById('next-btn').style.display = 'none';
            }

            if(lastLevel !== data.current_level) {
                lastLevel = data.current_level;
            }

            // Handle Endgame Leaderboard Popup Modal
            if(data.is_game_over) {
                document.getElementById('submit-btn').disabled = true;
                document.getElementById('guess-input').disabled = true;
                
                let tableRows = `<tr><th>Rank</th><th>Player Name</th><th>Lvl 1</th><th>Lvl 2</th><th>Lvl 3</th><th>Lvl 4</th><th>Lvl 5</th><th>Grand Total</th></tr>`;
                data.rankings.forEach((p, index) => {
                    tableRows += `<tr><td>#${index+1}</td><td>${p.name}</td><td>${p.lvls[0]}</td><td>${p.lvls[1]}</td><td>${p.lvls[2]}</td><td>${p.lvls[3]}</td><td>${p.lvls[4]}</td><td><strong>${p.total}</strong></td></tr>`;
                });
                document.getElementById('tree-body').innerHTML = tableRows;
                document.getElementById('score-overlay').style.display = 'flex';
            }
        }, 750);

        async function submitLetter() {
            let field = document.getElementById('guess-input');
            let char = field.value.trim().toUpperCase();
            field.value = "";
            field.focus();
            if(char.length === 1 && /[A-Z]/.test(char)) {
                await fetch('/guess', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ letter: char })
                });
            }
        }

        async function nextLevelRequest() {
            await fetch('/next', { method: 'POST' });
        }
    </script>
</head>
<body>

    <div id="auth-panel" class="auth-container">
        <h2 style="font-size:1.8rem; font-weight:bold; color:#FF007F; margin-top:0;">🎯 MULTIPLAYER HANGBOY LOBBY</h2>
        <div style="background:#11111B; border:1px solid #252538; padding:20px; border-radius:4px; margin:25px 0;">
            <p style="margin-top:0; font-size:1.1rem;">Enter Your Player Nickname:</p>
            <input type="text" id="nickname-input" class="text-field" style="width:80%; font-size:1.5rem;" maxlength="15" onkeydown="if(event.key==='Enter') registerUser()"><br><br>
            <button class="action-btn btn-join" onclick="registerUser()">LAUNCH MULTIPLAYER GAME MATCH</button>
        </div>
    </div>

    <div id="dashboard-panel" class="main-container">
        <div class="top-bar">
            <span id="player-lbl" style="color:#00E5FF;">👤 Player: ---</span>
            <div>
                <span id="level-lbl" style="color:#FFFF00; margin-right:20px;">Level: 1/5</span>
                <span id="lives-lbl" style="color:#FF477E;">❤️ Lives: 6/6</span>
            </div>
        </div>

        <div class="flex-split">
            <div class="canvas-panel">
                <canvas id="hangman-vector" width="220" height="260"></canvas>
            </div>
            <div class="controls-panel">
                <div class="card">
                    <span style="font-size:0.8rem; font-weight:bold; color:#A4A4C1;">💡 QUESTION HINT</span>
                    <div id="hint-txt" style="color:#00F5D4; font-size:1.1rem; font-style:italic; margin-top:5px;">Loading metrics...</div>
                </div>
                <div class="word-card">
                    <div id="word-lbl" class="word-lbl">_ _ _ _ _ _</div>
                </div>
                <div class="input-bar">
                    <span>Guess Letter:</span>
                    <input type="text" id="guess-input" class="text-field" style="width:50px; font-weight:bold;" maxlength="1" onkeydown="if(event.key==='Enter') submitLetter()">
                    <button id="submit-btn" class="action-btn btn-submit" onclick="submitLetter()">SUBMIT</button>
                    <button id="next-btn" class="action-btn btn-next" onclick="nextLevelRequest()">NEXT LEVEL ➡️</button>
                </div>
            </div>
        </div>

        <div style="text-align:left; margin-top:15px; padding:0 10px;">
            <span style="font-size:0.85rem; font-weight:bold; color:#A4A4C1;">💬 Transmission Logs:</span>
            <div id="logs-stream" class="log-box"></div>
        </div>
    </div>

    <div id="score-overlay" class="leaderboard-overlay">
        <div class="leaderboard-modal">
            <h2 style="color:#FFFF00; margin-top:0; letter-spacing:2px;">🏆 TOURNAMENT FINAL RANKINGS</h2>
            <table id="tree-body" class="tree-table"></table>
            <br>
            <button class="action-btn" style="background:#FF007F; color:white; padding:10px 30px;" onclick="location.reload()">DISMISS SCOREBOARD & RESTART</button>
        </div>
    </div>

</body>
</html>
"""

# --- Router Controllers ---
@app.route('/', methods=['GET'])
def homepage():
    return render_template_string(HTML_TEMPLATE)

@app.route('/join', methods=['POST'])
def process_handshake():
    data = request.get_json() or {}
    name = data.get('name', '').strip().upper()
    if not name:
        return jsonify({"success": False})
    
    session['username'] = name
    with state_lock:
        if name not in scores:
            scores[name] = [0, 0, 0, 0, 0]
            game_state["system_logs"].append(f"📡 [CONNECTED] Player '{name}' synchronized successfully.")
            game_state["system_logs"].append(f"📢 Player '{name}' synchronized into lobby.")
    return jsonify({"success": True})

@app.route('/state', methods=['GET'])
def fetch_synchronized_broker():
    with state_lock:
        return jsonify({
            "revealed_word": " ".join(game_state["revealed_word"]),
            "global_lives": game_state["global_lives"],
            "hint": game_state["hint"],
            "current_level": game_state["current_level"],
            "is_game_over": game_state["is_game_over"],
            "system_logs": game_state["system_logs"],
            "rankings": get_rankings_array()
        })

@app.route('/guess', methods=['POST'])
def receive_client_guess():
    data = request.get_json() or {}
    char = data.get('letter', '').upper()
    player_name = session.get('username', 'ANONYMOUS')
    current_lvl_idx = game_state["current_level"]

    with state_lock:
        if game_state["global_lives"] > 0 and "_" in game_state["revealed_word"] and not game_state["is_game_over"]:
            if char in game_state["secret_word"]:
                correct_hit = False
                for idx, letter in enumerate(game_state["secret_word"]):
                    if letter == char and game_state["revealed_word"][idx] == "_":
                        game_state["revealed_word"][idx] = char
                        correct_hit = True
                
                if correct_hit:
                    scores[player_name][current_lvl_idx] += 15
                    game_state["system_logs"].append(f"🎯 {player_name} solved '{char}'! (+15 pts)")
                else:
                    game_state["system_logs"].append(f"ℹ️ Character '{char}' was already solved.")
            else:
                game_state["global_lives"] -= 1
                game_state["system_logs"].append(f"❌ {player_name} guessed '{char}' incorrectly! (-1 Life)")

            # Check Level Cleared Boundary
            if "_" not in game_state["revealed_word"]:
                scores[player_name][current_lvl_idx] += 50
                if game_state["current_level"] + 1 >= len(words_pool):
                    game_state["is_game_over"] = True
                    game_state["system_logs"].append("🏁 TOURNAMENT COMPLETED! Game Over. Grand ranking table generated.")
                else:
                    game_state["system_logs"].append(f"🎉 LEVEL {current_lvl_idx+1} CLEARED! (+50 bonus points to {player_name}). Click 'Next Level'.")
            
            # Check Match Loss Boundary
            elif game_state["global_lives"] <= 0:
                game_state["is_game_over"] = True
                game_state["system_logs"].append(f"💀 MATCH FAILED! No lives left. Target word was: '{game_state['secret_word']}'.")

    return jsonify({"status": "processed"})

@app.route('/next', methods=['POST'])
def process_advancement_request():
    player_name = session.get('username', 'ANONYMOUS')
    with state_lock:
        if game_state["current_level"] + 1 < len(words_pool) and "_" not in game_state["revealed_word"]:
            game_state["current_level"] += 1
            load_level()
            game_state["system_logs"].append(f"🔄 {player_name} moved the team forward to Level {game_state['current_level'] + 1}!")
    return jsonify({"status": "advanced"})

if __name__ == '__main__':
    # Binds on port 8080 just like your original server setup!
    app.run(host='0.0.0.0', port=8080, debug=True)