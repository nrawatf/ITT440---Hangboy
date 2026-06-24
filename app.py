from flask import Flask, render_template_string, request, jsonify, session
import time

app = Flask(__name__)
# Secret key wajib untuk pastikan data session disimpan selamat dalam browser pemain
app.secret_key = "itt440_super_secret_hangboy_key_production_v3"

# 🎯 Pool Perkataan Kejohanan (Sama untuk semua, tapi progress berasingan)
words_pool = [
    {"word": "CHALLENGE", "hint": "A task or situation that tests someone's abilities."},
    {"word": "JOURNEY", "hint": "An act of traveling from one place to another."},
    {"word": "HORIZON", "hint": "The line at which the earth's surface and the sky appear to meet."},
    {"word": "MYSTERY", "hint": "Something that is difficult or impossible to understand or explain."},
    {"word": "VICTORY", "hint": "An act of defeating an enemy or opponent."}
]

def init_player_game(username):
    """Menyediakan state game yang 100% asing untuk pemain baru"""
    session["username"] = username
    session["current_level"] = 0
    session["secret_word"] = words_pool[0]["word"]
    session["hint"] = words_pool[0]["hint"]
    session["revealed_word"] = ["_" for _ in words_pool[0]["word"]]
    session["lives"] = 6
    session["is_game_over"] = False
    session["start_time"] = time.time()
    session["elapsed_time"] = 0.0
    session["logs"] = [f"📡 Player '{username}' joined! Game started."]

# 🏆 Shared Global Leaderboard (Hanya untuk simpan rekod masa bila dah menang)
global_leaderboard = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Multiplayer Hangboy</title>
    <style>
        body { background-color: #1E1E2E; color: #F8F8F2; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin: 0; padding: 20px; }
        .auth-box { max-width: 450px; margin: 100px auto; background: #252538; padding: 30px; border-radius: 8px; border: 2px solid #FF007F; }
        .game-box { max-width: 900px; margin: 20px auto; display: none; }
        .top-stats { background: #252538; padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 20px; font-size: 1.1rem; }
        .game-split { display: flex; gap: 20px; justify-content: center; }
        .panel-g { background: #11111B; border: 2px solid #FF007F; padding: 20px; width: 240px; height: 300px; display: flex; align-items: center; justify-content: center; }
        .panel-c { flex-grow: 1; display: flex; flex-direction: column; gap: 15px; }
        .card { background: #11111B; padding: 15px; border-radius: 4px; text-align: left; border: 1px solid #252538; }
        .word-display { background: #252538; padding: 25px; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 2.5rem; letter-spacing: 8px; color: #FFFF00; font-weight: bold; }
        input.letter-in { background: #11111B; border: 1px solid #A4A4C1; color: #FFFF00; font-size: 1.5rem; width: 60px; text-align: center; padding: 5px; border-radius: 4px; font-weight: bold; }
        button.btn { font-weight: bold; font-size: 1rem; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-join { background: #00F5D4; color: #1E1E2E; width: 100%; font-size: 1.2rem; }
        .btn-sub { background: #00F5D4; color: #1E1E2E; }
        .btn-next { background: #FF007F; color: white; display: none; }
        .logs { background: #11111B; border: 1px solid #A4A4C1; font-family: 'Consolas', monospace; font-size: 0.9rem; color: #A4A4C1; padding: 10px; height: 110px; overflow-y: auto; text-align: left; border-radius: 4px; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(17,17,27,0.96); align-items: center; justify-content: center; z-index: 1000; }
        .modal { background: #11111B; border: 2px solid #FF007F; padding: 30px; border-radius: 8px; width: 80%; max-width: 650px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { background: #252538; padding: 10px; border: 1px solid #1E1E2E; text-align: center; }
        th { background: #1E1E2E; color: #00F5D4; }
    </style>
    <script>
        let playing = false;

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
            if(lives <= 4) { ctx.beginPath(); ctx.moveTo(140, 100); ctx.lineTo(140, 170); ctx.stroke(); }
            if(lives <= 3) { ctx.beginPath(); ctx.moveTo(140, 120); ctx.lineTo(110, 140); ctx.stroke(); }
            if(lives <= 2) { ctx.beginPath(); ctx.moveTo(140, 120); ctx.lineTo(170, 140); ctx.stroke(); }
            if(lives <= 1) { ctx.beginPath(); ctx.moveTo(140, 170); ctx.lineTo(110, 210); ctx.stroke(); }
            if(lives <= 0) { 
                ctx.strokeStyle = "#FF477E"; ctx.beginPath(); ctx.moveTo(140, 170); ctx.lineTo(170, 210); ctx.stroke(); 
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
            }
        }

        // Loop update hantar data berasingan setiap 400ms
        setInterval(async () => {
            if(!playing) return;
            let res = await fetch('/update_state');
            let data = await res.json();
            if(data.status === 'expired') return;

            document.getElementById('word-space').innerText = data.revealed_word;
            document.getElementById('hint-space').innerText = data.hint;
            document.getElementById('lvl-space').innerText = "Level: " + (data.current_level + 1) + "/5";
            document.getElementById('lives-space').innerText = "❤️ Lives: " + data.lives + "/6";
            document.getElementById('timer-space').innerText = "⏱️ Time: " + data.elapsed_time + "s";
            
            drawHangman(data.lives);

            document.getElementById('log-stream').innerHTML = data.logs.map(l => ">> " + l).join("<br>");
            document.getElementById('log-stream').scrollTop = document.getElementById('log-stream').scrollHeight;

            if(!data.revealed_word.includes('_') && data.current_level < 4) {
                document.getElementById('next-btn').style.display = 'inline-block';
            } else {
                document.getElementById('next-btn').style.display = 'none';
            }

            if(data.is_game_over) {
                document.getElementById('sub-btn').disabled = true;
                document.getElementById('letter-box').disabled = true;
                let rows = `<tr><th>Rank</th><th>Player</th><th>Result</th><th>Time Taken</th></tr>`;
                data.leaderboard.forEach((p, idx) => {
                    rows += `<tr><td>#${idx+1}</td><td>${p.name}</td><td>${p.success ? '🏁 Won' : '💀 Lost'}</td><td><strong>${p.time}s</strong></td></tr>`;
                });
                document.getElementById('table-body').innerHTML = rows;
                document.getElementById('end-overlay').style.display = 'flex';
            }
        }, 400);

        async function sendLetter() {
            let box = document.getElementById('letter-box');
            let val = box.value.trim().toUpperCase();
            box.value = ""; box.focus();
            if(val.length === 1 && /[A-Z]/.test(val)) {
                await fetch('/guess_letter', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ letter: val })
                });
            }
        }

        async function triggerNext() {
            await fetch('/go_next', { method: 'POST' });
        }
    </script>
</head>
<body>

    <!-- Auth View -->
    <div id="auth-view" class="auth-box">
        <h2 style="color: #FF007F; margin-top: 0;">🎯 MULTIPLAYER HANGBOY</h2>
        <p>Setiap pemain akan dapat papan permainan dan timer berasingan secara adil!</p>
        <input type="text" id="name-in" class="letter-in" style="width: 80%; font-size: 1.3rem;" placeholder="NICKNAME" maxlength="12" onkeydown="if(event.key==='Enter') joinLobby()">
        <br><br>
        <button class="btn btn-join" onclick="joinLobby()">START MY TOURNAMENT</button>
    </div>

    <!-- Game View -->
    <div id="game-view" class="game-box">
        <div class="top-stats">
            <span id="p-name" style="color: #00E5FF;">👤 Player: </span>
            <div>
                <span id="timer-space" style="color: #00F5D4; margin-right: 20px;">⏱️ Time: 0.0s</span>
                <span id="lvl-space" style="color: #FFFF00; margin-right: 20px;">Level: 1/5</span>
                <span id="lives-space" style="color: #FF477E;">❤️ Lives: 6/6</span>
            </div>
        </div>

        <div class="game-split">
            <div class="panel-g">
                <canvas id="g-canvas" width="200" height="250"></canvas>
            </div>
            <div class="panel-c">
                <div class="card">
                    <small style="color: #A4A4C1; font-weight: bold;">💡 HINT QUESTION:</small>
                    <div id="hint-space" style="color: #00F5D4; font-size: 1.1rem; margin-top: 5px;"></div>
                </div>
                <div id="word-space" class="word-display">_ _ _ _</div>
                <div>
                    <span>Guess: </span>
                    <input type="text" id="letter-box" class="letter-in" maxlength="1" onkeydown="if(event.key==='Enter') sendLetter()">
                    <button id="sub-btn" class="btn btn-sub" onclick="sendLetter()">SUBMIT</button>
                    <button id="next-btn" class="btn btn-next" onclick="triggerNext()">NEXT LEVEL ➡️</button>
                </div>
            </div>
        </div>

        <div style="text-align: left; margin-top: 20px;">
            <small style="color: #A4A4C1; font-weight: bold;">💬 Secret Transmission Logs:</small>
            <div id="log-stream" class="logs"></div>
        </div>
    </div>

    <!-- Scoreboard Overlay -->
    <div id="end-overlay" class="overlay">
        <div class="modal">
            <h2 style="color: #FFFF00; margin-top:0;">🏆 TOURNAMENT RESULTS (FASTEST WINS)</h2>
            <table id="table-body"></table>
            <br>
            <button class="btn" style="background: #FF007F; color: white;" onclick="location.reload()">PLAY AGAIN</button>
        </div>
    </div>

</body>
</html>
"""

@app.route('/')
def main_index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start_game():
    req = request.get_json() or {}
    username = req.get('username', '').strip().upper()
    if not username:
        return jsonify({"status": "error"})
    init_player_game(username)
    return jsonify({"status": "ok"})

@app.route('/update_state', methods=['GET'])
def update_state():
    if "username" not in session:
        return jsonify({"status": "expired"})
    
    if not session.get("is_game_over", False):
        session["elapsed_time"] = round(time.time() - session["start_time"], 2)
        
    sorted_leaderboard = sorted(global_leaderboard, key=lambda x: (-int(x["success"]), x["time"]))
    
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
        session["logs"].append(f"Wrong! '{char}' is not in the word. (-1 Life)")
    
    session["revealed_word"] = revealed

    # Check Win
    if "_" not in revealed:
        if session["current_level"] + 1 >= len(words_pool):
            session["is_game_over"] = True
            session["elapsed_time"] = round(time.time() - session["start_time"], 2)
            global_leaderboard.append({
                "name": session["username"],
                "time": session["elapsed_time"],
                "success": True
            })
        else:
            session["logs"].append("Level completed! Click Next Level.")
            
    # Check Lose
    elif session["lives"] <= 0:
        session["is_game_over"] = True
        session["elapsed_time"] = round(time.time() - session["start_time"], 2)
        global_leaderboard.append({
            "name": session["username"],
            "time": session["elapsed_time"],
            "success": False
        })
        session["logs"].append(f"Game Over! The word was {secret}")
        
    return jsonify({"status": "processed"})

@app.route('/go_next', methods=['POST'])
def go_next():
    if "username" in session and "_" not in session["revealed_word"]:
        if session["current_level"] + 1 < len(words_pool):
            session["current_level"] += 1
            lvl = session["current_level"]
            session["secret_word"] = words_pool[lvl]["word"]
            session["hint"] = words_pool[lvl]["hint"]
            session["revealed_word"] = ["_" for _ in words_pool[lvl]["word"]]
            session["lives"] = 6
            session["logs"].append(f"Advanced to Level {lvl + 1}!")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)