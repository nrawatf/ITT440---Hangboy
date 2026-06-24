from flask import Flask, render_template_string, request, jsonify, session
import time

app = Flask(__name__)
# Unique secret key to manage isolated candidate player sessions cleanly
app.secret_key = "itt440_ultimate_hangman_session_key_admin_v7"

# 🎯 Official Tournament Word Pool (In English with English Hints)
words_pool = [
    {"word": "CHALLENGE", "hint": "A task or situation that tests someone's abilities."},
    {"word": "JOURNEY", "hint": "An act of traveling from one place to another."},
    {"word": "HORIZON", "hint": "The line at which the earth's surface and the sky appear to meet."},
    {"word": "MYSTERY", "hint": "Something that is difficult or impossible to understand or explain."},
    {"word": "VICTORY", "hint": "An act of defeating an enemy or opponent."}
]

# Shared Global State for Central Administrator Tracking
active_players = {}

def update_admin_tracker():
    """Cleans up inactive sessions and keeps active player data fresh"""
    now = time.time()
    # If a player hasn't sent an update in 8 seconds, they are considered disconnected
    to_delete = [uid for uid, p in active_players.items() if now - p["last_seen"] > 8]
    for uid in to_delete:
        del active_players[uid]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ITT440 Hangboy Tournament</title>
    <style>
        body { background-color: #1E1E2E; color: #F8F8F2; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin: 0; padding: 15px; }
        .auth-box { max-width: 450px; margin: 80px auto; background: #252538; padding: 30px; border-radius: 8px; border: 2px solid #FF007F; }
        .game-box { max-width: 850px; margin: 10px auto; display: none; }
        .top-stats { background: #252538; padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 15px; font-size: 1.1rem; }
        .game-split { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .panel-g { background: #11111B; border: 2px solid #FF007F; padding: 15px; width: 220px; height: 280px; display: flex; align-items: center; justify-content: center; border-radius: 6px; }
        .panel-c { flex-grow: 1; display: flex; flex-direction: column; gap: 12px; min-width: 280px; }
        .card { background: #11111B; padding: 12px; border-radius: 4px; text-align: left; border: 1px solid #252538; }
        .word-display { background: #252538; padding: 20px; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 2.3rem; letter-spacing: 6px; color: #FFFF00; font-weight: bold; }
        input.letter-in { background: #11111B; border: 2px solid #00F5D4; color: #FFFF00; font-size: 1.6rem; width: 60px; text-align: center; padding: 5px; border-radius: 4px; font-weight: bold; }
        .btn { font-weight: bold; font-size: 1rem; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-join { background: #00F5D4; color: #1E1E2E; width: 100%; font-size: 1.2rem; margin-top: 10px; }
        .btn-sub { background: #00F5D4; color: #1E1E2E; }
        .btn-next { background: #FF007F; color: white; display: none; }
        .logs { background: #11111B; border: 1px solid #44475A; font-family: 'Consolas', monospace; font-size: 0.9rem; color: #A4A4C1; padding: 10px; height: 95px; overflow-y: auto; text-align: left; border-radius: 4px; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(17,17,27,0.96); align-items: center; justify-content: center; z-index: 1000; }
        .modal { background: #11111B; border: 2px solid #FF007F; padding: 25px; border-radius: 8px; width: 90%; max-width: 600px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { background: #252538; padding: 10px; border: 1px solid #1E1E2E; text-align: center; }
        th { background: #1E1E2E; color: #00F5D4; }
    </style>
    <script>
        let playing = false;
        let fetchLock = false;
        let clientStartTime = 0;
        let clientBaseElapsed = 0;
        let localTimerInterval = null;

        function drawHangman(lives) {
            const canvas = document.getElementById('g-canvas');
            if(!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = "#F8F8F2"; ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(20, 240); ctx.lineTo(180, 240); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(60, 240); ctx.lineTo(60, 30); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(60, 30); ctx.lineTo(140, 30); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(140, 30); ctx.lineTo(140, 60); ctx.stroke();
            ctx.strokeStyle = "#00F5D4";
            if(lives <= 5) { ctx.beginPath(); ctx.arc(140, 80, 20, 0, Math.PI*2); ctx.stroke(); }
            if(lives <= 4) { ctx.beginPath(); ctx.moveTo(140, 100); ctx.lineTo(140, 160); ctx.stroke(); }
            if(lives <= 3) { ctx.beginPath(); ctx.moveTo(140, 120); ctx.lineTo(110, 140); ctx.stroke(); }
            if(lives <= 2) { ctx.beginPath(); ctx.moveTo(140, 120); ctx.lineTo(170, 140); ctx.stroke(); }
            if(lives <= 1) { ctx.beginPath(); ctx.moveTo(140, 160); ctx.lineTo(110, 200); ctx.stroke(); }
            if(lives <= 0) { 
                ctx.strokeStyle = "#FF477E"; ctx.beginPath(); ctx.moveTo(140, 160); ctx.lineTo(170, 200); ctx.stroke(); 
            }
        }

        async function joinLobby() {
            let name = document.getElementById('name-in').value.trim().toUpperCase();
            if(!name) return alert("Please enter your nickname!");
            let res = await fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: name })
            });
            let data = await res.json();
            if(data.status === 'ok') {
                playing = true;
                document.getElementById('auth-view').style.display = 'none';
                document.getElementById('game-view').style.display = 'block';
                document.getElementById('p-name').innerText = "👤 Player: " + name;
                document.getElementById('letter-box').focus();
                
                clientStartTime = Date.now();
                clientBaseElapsed = 0;
                startLocalTimer();
            }
        }

        function startLocalTimer() {
            if(localTimerInterval) clearInterval(localTimerInterval);
            localTimerInterval = setInterval(() => {
                if(!playing) return;
                let currentSessionDiff = (Date.now() - clientStartTime) / 1000;
                let realisticTime = (clientBaseElapsed + currentSessionDiff).toFixed(1);
                document.getElementById('timer-space').innerText = "⏱️ Time: " + realisticTime + "s";
            }, 100);
        }

        // Optimized state synchronization polling for lag-free rendering
        setInterval(async () => {
            if(!playing || fetchLock) return;
            try {
                let res = await fetch('/update_state');
                let data = await res.json();
                if(data.status === 'expired') return;

                document.getElementById('word-space').innerText = data.revealed_word;
                document.getElementById('hint-space').innerText = data.hint;
                document.getElementById('lvl-space').innerText = "Level: " + (data.current_level + 1) + "/5";
                document.getElementById('lives-space').innerText = "❤️ Lives: " + data.lives + "/6";
                
                clientBaseElapsed = data.elapsed_time;
                clientStartTime = Date.now();
                
                drawHangman(data.lives);

                document.getElementById('log-stream').innerHTML = data.logs.map(l => ">> " + l).join("<br>");
                document.getElementById('log-stream').scrollTop = document.getElementById('log-stream').scrollHeight;

                if(!data.revealed_word.includes('_') && data.current_level < 4) {
                    document.getElementById('next-btn').style.display = 'inline-block';
                } else {
                    document.getElementById('next-btn').style.display = 'none';
                }

                if(data.is_game_over) {
                    playing = false;
                    clearInterval(localTimerInterval);
                    document.getElementById('sub-btn').disabled = true;
                    document.getElementById('letter-box').disabled = true;
                    
                    let rows = `<tr><th>Rank</th><th>Player</th><th>Status</th><th>Total Time Taken</th></tr>`;
                    data.leaderboard.forEach((p, idx) => {
                        rows += `<tr><td>#${idx+1}</td><td>${p.name}</td><td>${p.status}</td><td><strong>${p.time.toFixed(1)}s</strong></td></tr>`;
                    });
                    document.getElementById('table-body').innerHTML = rows;
                    document.getElementById('end-overlay').style.display = 'flex';
                }
            } catch(e) {}
        }, 1000);

        async function sendLetter() {
            let box = document.getElementById('letter-box');
            let val = box.value.trim().toUpperCase();
            box.value = ""; box.focus();
            if(val.length === 1 && /[A-Z]/.test(val)) {
                fetchLock = true;
                let res = await fetch('/guess_letter', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ letter: val })
                });
                let data = await res.json();
                
                document.getElementById('word-space').innerText = data.revealed_word;
                document.getElementById('lives-space').innerText = "❤️ Lives: " + data.lives + "/6";
                drawHangman(data.lives);
                fetchLock = false;
            }
        }

        async function triggerNext() {
            fetchLock = true;
            await fetch('/go_next', { method: 'POST' });
            document.getElementById('next-btn').style.display = 'none';
            fetchLock = false;
        }
    </script>
</head>
<body>

    <div id="auth-view" class="auth-box">
        <h2 style="color: #FF007F; margin-top: 0; font-size: 1.6rem;">🎯 ITT440 HANGBOY TOURNAMENT</h2>
        <p style="font-size: 0.95rem; color: #A4A4C1;">Supports multiple players playing simultaneously with Live Admin Monitoring Dashboard!</p>
        <input type="text" id="name-in" class="letter-in" style="width: 85%; font-size: 1.3rem;" placeholder="NICKNAME" maxlength="12" onkeydown="if(event.key==='Enter') joinLobby()">
        <br>
        <button class="btn btn-join" onclick="joinLobby()">START TOURNAMENT</button>
    </div>

    <div id="game-view" class="game-box">
        <div class="top-stats">
            <span id="p-name" style="color: #00E5FF;">👤 Player: </span>
            <div>
                <span id="timer-space" style="color: #00F5D4; margin-right: 15px;">⏱️ Time: 0.0s</span>
                <span id="lvl-space" style="color: #FFFF00; margin-right: 15px;">Level: 1/5</span>
                <span id="lives-space" style="color: #FF477E;">❤️ Lives: 6/6</span>
            </div>
        </div>

        <div class="game-split">
            <div class="panel-g">
                <canvas id="g-canvas" width="180" height="250"></canvas>
            </div>
            <div class="panel-c">
                <div class="card">
                    <small style="color: #A4A4C1; font-weight: bold;">💡 QUESTION HINT:</small>
                    <div id="hint-space" style="color: #00F5D4; font-size: 1.05rem; margin-top: 5px;"></div>
                </div>
                <div id="word-space" class="word-display">_ _ _ _</div>
                <div>
                    <span style="font-size: 1.1rem;">Guess Letter: </span>
                    <input type="text" id="letter-box" class="letter-in" maxlength="1" onkeydown="if(event.key==='Enter') sendLetter()">
                    <button id="sub-btn" class="btn btn-sub" onclick="sendLetter()">SUBMIT</button>
                    <button id="next-btn" class="btn btn-next" onclick="triggerNext()">NEXT LEVEL ➡️</button>
                </div>
            </div>
        </div>

        <div style="text-align: left; margin-top: 15px;">
            <small style="color: #A4A4C1; font-weight: bold;">💬 Live Transmission Logs:</small>
            <div id="log-stream" class="logs"></div>
        </div>
    </div>

    <div id="end-overlay" class="overlay">
        <div class="modal">
            <h2 style="color: #FFFF00; margin-top:0; font-size: 1.5rem;">🏆 TOURNAMENT SCOREBOARD (FASTEST RUNTIME WINS)</h2>
            <table id="table-body"></table>
            <br>
            <button class="btn" style="background: #FF007F; color: white;" onclick="location.reload()">PLAY AGAIN</button>
        </div>
    </div>

</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🚨 TOURNAMENT LIVE ADMIN PANEL</title>
    <style>
        body { background-color: #0D0E15; color: #F8F8F2; font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; text-align: center; }
        .container { max-width: 1000px; margin: 0 auto; }
        .grid { display: flex; gap: 20px; margin-top: 25px; justify-content: center; flex-wrap: wrap; }
        .box { background: #1E1E2E; border: 2px solid #00F5D4; padding: 20px; border-radius: 8px; flex: 1; min-width: 300px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .box.leaderboard { border-color: #FF007F; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; border: 1px solid #252538; text-align: center; background: #11111B; }
        th { background: #252538; color: #FFFF00; font-weight: bold; }
        .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
        .badge.playing { background: #00F5D4; color: #1E1E2E; }
        .badge.won { background: #FF007F; color: white; }
        .badge.lost { background: #FF477E; color: white; }
    </style>
    <script>
        // Automatic Real-Time Live Admin Scoreboard updates every 1 second
        setInterval(async () => {
            try {
                let res = await fetch('/admin/data');
                let data = await res.json();
                
                // 1. Update Active Players list
                let activeRows = `<tr><th>Player Name</th><th>Current Level</th><th>Lives Left</th><th>Live Timer</th><th>Status</th></tr>`;
                if(data.players.length === 0) {
                    activeRows += `<tr><td colspan="5" style="color:#A4A4C1;">No active players online right now.</td></tr>`;
                } else {
                    data.players.forEach(p => {
                        activeRows += `<tr>
                            <td style="color:#00E5FF; font-weight:bold;">${p.name}</td>
                            <td>Level ${p.level + 1}/5</td>
                            <td style="color:#FF477E; font-weight:bold;">❤️ ${p.lives}/6</td>
                            <td style="color:#FFFF00;"><strong>${p.time.toFixed(1)}s</strong></td>
                            <td><span class="badge ${p.status.toLowerCase()}">${p.status}</span></td>
                        </tr>`;
                    });
                }
                document.getElementById('active-table').innerHTML = activeRows;

                // 2. Update Live Ranked Scoreboard
                let scoreRows = `<tr><th>Rank</th><th>Player Name</th><th>Final Status</th><th>Final Time Record</th></tr>`;
                if(data.leaderboard.length === 0) {
                    scoreRows += `<tr><td colspan="4" style="color:#A4A4C1;">No submissions yet. Game in progress!</td></tr>`;
                } else {
                    data.leaderboard.forEach((l, idx) => {
                        scoreRows += `<tr>
                            <td>#${idx+1}</td>
                            <td style="font-weight:bold;">${l.name}</td>
                            <td><span class="badge ${l.status.toLowerCase()}">${l.status}</span></td>
                            <td style="color:#00F5D4;"><strong>${l.time.toFixed(2)}s</strong></td>
                        </tr>`;
                    });
                }
                document.getElementById('score-table').innerHTML = scoreRows;
            } catch(e){}
        }, 1000);
    </script>
</head>
<body>
    <div class="container">
        <h1 style="color: #00F5D4; margin-bottom: 5px;">🚨 ITT440 TOURNAMENT LIVE CENTRAL</h1>
        <p style="color: #A4A4C1; margin-top: 0;">Real-time administrator monitor station. Tracks every candidate instantaneously.</p>
        
        <div class="grid">
            <div class="box">
                <h3 style="margin-top:0; color:#00F5D4;">👥 ONLINE CANDIDATES IN-GAME</h3>
                <table id="active-table"></table>
            </div>
            <div class="box leaderboard">
                <h3 style="margin-top:0; color:#FF007F;">🏆 LIVE TOURNAMENT LEADERBOARD</h3>
                <table id="score-table"></table>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def main_index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/admin')
def admin_dashboard():
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/admin/data')
def admin_data_api():
    update_admin_tracker()
    player_list = []
    for uid, p in active_players.items():
        curr_time = p["elapsed_time"] if p["is_game_over"] else (time.time() - p["start_time"])
        status_str = "Playing"
        if p["is_game_over"]:
            status_str = "Won" if "_" not in p["revealed_word"] else "Lost"
            
        player_list.append({
            "name": p["username"],
            "level": p["current_level"],
            "lives": p["lives"],
            "time": curr_time,
            "status": status_str
        })
        
    leaderboard_list = []
    for uid, p in active_players.items():
        curr_time = p["elapsed_time"] if p["is_game_over"] else (time.time() - p["start_time"])
        status_str = "Playing"
        if p["is_game_over"]:
            status_str = "Won" if "_" not in p["revealed_word"] else "Lost"
        
        leaderboard_list.append({
            "name": p["username"],
            "time": curr_time,
            "status": status_str,
            "success": (p["is_game_over"] and "_" not in p["revealed_word"])
        })
    
    # Sort rule: Winners first (Rank 1), then Active Players, sorted by lowest time taken
    sorted_leaderboard = sorted(leaderboard_list, key=lambda x: (-int(x["status"] == "Won"), int(x["status"] == "Playing"), x["time"]))

    return jsonify({
        "players": player_list,
        "leaderboard": sorted_leaderboard
    })

@app.route('/start', methods=['POST'])
def start_game():
    req = request.get_json() or {}
    username = req.get('username', '').strip().upper()
    if not username:
        return jsonify({"status": "error"})
        
    session["username"] = username
    session["player_id"] = username + "_" + str(int(time.time()))
    session["current_level"] = 0
    session["secret_word"] = words_pool[0]["word"]
    session["hint"] = words_pool[0]["hint"]
    session["revealed_word"] = ["_" for _ in words_pool[0]["word"]]
    session["lives"] = 6
    session["is_game_over"] = False
    session["start_time"] = time.time()
    session["elapsed_time"] = 0.0
    session["logs"] = [f"📡 Player '{username}' joined the tournament! Level 1 started."]
    
    active_players[session["player_id"]] = {
        "username": username,
        "current_level": 0,
        "lives": 6,
        "start_time": session["start_time"],
        "elapsed_time": 0.0,
        "is_game_over": False,
        "revealed_word": session["revealed_word"],
        "last_seen": time.time()
    }
    return jsonify({"status": "ok"})

@app.route('/update_state', methods=['GET'])
def update_state():
    if "username" not in session or "player_id" not in session:
        return jsonify({"status": "expired"})
    
    pid = session["player_id"]
    if not session.get("is_game_over", False):
        session["elapsed_time"] = time.time() - session["start_time"]
    
    if pid in active_players:
        active_players[pid]["elapsed_time"] = session["elapsed_time"]
        active_players[pid]["last_seen"] = time.time()
        
    leaderboard_list = []
    for uid, p in active_players.items():
        curr_time = p["elapsed_time"] if p["is_game_over"] else (time.time() - p["start_time"])
        stat = "Playing"
        if p["is_game_over"]:
            stat = "Won" if "_" not in p["revealed_word"] else "Lost"
        leaderboard_list.append({"name": p["username"], "time": curr_time, "status": stat, "won": stat == "Won"})
        
    sorted_leaderboard = sorted(leaderboard_list, key=lambda x: (-int(x["won"]), x["status"] == "Playing", x["time"]))
    
    return jsonify({
        "revealed_word": " ".join(session["revealed_word"]),
        "lives": session["lives"],
        "hint": session["hint"],
        "current_level": session["current_level"],
        "is_game_over": session["is_game_over"],
        "elapsed_time": session["elapsed_time"],
        "logs": session["logs"],
        "leaderboard": sorted_leaderboard
    })

@app.route('/guess_letter', methods=['POST'])
def guess_letter():
    if "username" not in session or session.get("is_game_over", False):
        return jsonify({"status": "ignored"})
        
    req = request.get_json() or {}
    char = req.get('letter', '').upper()
    pid = session["player_id"]
    
    secret = session["secret_word"]
    revealed = session["revealed_word"]
    
    if char in secret:
        hit = False
        for i, l in enumerate(secret):
            if l == char and revealed[i] == "_":
                revealed[i] = char
                hit = True
        if hit:
            session["logs"].append(f"Correct! Found letter '{char}'")
    else:
        session["lives"] -= 1
        session["logs"].append(f"Wrong! Letter '{char}' is not in the word. (-1 Life)")
    
    session["revealed_word"] = revealed
    
    if pid in active_players:
        active_players[pid]["revealed_word"] = revealed
        active_players[pid]["lives"] = session["lives"]

    if "_" not in revealed:
        if session["current_level"] + 1 >= len(words_pool):
            session["is_game_over"] = True
            session["elapsed_time"] = time.time() - session["start_time"]
            session["logs"].append("🎉 Victory! You completed the tournament!")
            if pid in active_players:
                active_players[pid]["is_game_over"] = True
                active_players[pid]["elapsed_time"] = session["elapsed_time"]
        else:
            session["logs"].append("Level completed! Click 'Next Level' button.")
            
    elif session["lives"] <= 0:
        session["is_game_over"] = True
        session["elapsed_time"] = time.time() - session["start_time"]
        session["logs"].append(f"💀 Game Over! The hidden word was: {secret}")
        if pid in active_players:
            active_players[pid]["is_game_over"] = True
            active_players[pid]["elapsed_time"] = session["elapsed_time"]
        
    return jsonify({
        "revealed_word": " ".join(session["revealed_word"]),
        "lives": session["lives"]
    })

@app.route('/go_next', methods=['POST'])
def go_next():
    if "username" in session and "_" not in session["revealed_word"]:
        pid = session["player_id"]
        if session["current_level"] + 1 < len(words_pool):
            session["current_level"] += 1
            lvl = session["current_level"]
            session["secret_word"] = words_pool[lvl]["word"]
            session["hint"] = words_pool[lvl]["hint"]
            session["revealed_word"] = ["_" for _ in words_pool[lvl]["word"]]
            session["lives"] = 6
            session["logs"].append(f"Advanced into Level {lvl + 1}!")
            
            if pid in active_players:
                active_players[pid]["current_level"] = lvl
                active_players[pid]["revealed_word"] = session["revealed_word"]
                active_players[pid]["lives"] = 6
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)