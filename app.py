from flask import Flask, render_template_string, jsonify, request, session
import socket
import time

# Fungsi helper pembungkusan mesej mengikut protokol tugasan anda
def send_msg(sock, msg):
    try:
        encoded_msg = msg.encode('utf-8')
        msg_len = len(encoded_msg)
        # Menghantar header 4-byte panjang mesej diikuti oleh kandungan mesej
        sock.sendall(msg_len.to_bytes(4, byteorder='big') + encoded_msg)
    except Exception:
        pass

def recv_msg(sock):
    try:
        # Membaca header 4-byte untuk mengetahui panjang mesej sebenar
        raw_msglen = sock.recv(4)
        if not raw_msglen:
            return None
        msglen = int.from_bytes(raw_msglen, byteorder='big')
        
        # Mengambil keseluruhan kandungan mesej berdasarkan panjang yang dibaca
        chunks = []
        bytes_recd = 0
        while bytes_recd < msglen:
            chunk = sock.recv(min(msglen - bytes_recd, 2048))
            if chunk == b'':
                break
            chunks.append(chunk)
            bytes_recd += len(chunk)
        return b''.join(chunks).decode('utf-8')
    except Exception:
        return None

app = Flask(__name__)
# Menggunakan session secret key baharu seperti dalam repo GitHub anda (image_cd1325.png)
app.secret_key = "itt440_ultimate_hangman_session_key_admin_v1"

# 🎯 TOURNAMENT MASTER WORD POOL (Struktur data rasmi tugasan anda)
master_words_pool = [
    {"word": "CHALLENGE", "hint": "A task or situation that tests someone's abilities."},
    {"word": "JOURNEY", "hint": "An act of traveling from one place to another."},
    {"word": "HORIZON", "hint": "The line at which the earth's surface and the sky appear to meet."},
    {"word": "MYSTERY", "hint": "Something that is difficult or impossible to understand or explain."},
    {"word": "VICTORY", "hint": "An act of defeating an enemy or opponent."},
    {"word": "ADVENTURE", "hint": "An exciting or very unusual and risky experience."},
    {"word": "CHAMPION", "hint": "A person who has defeated all rivals in a competition."},
    {"word": "FESTIVAL", "hint": "A day or period of celebration, typically a religious or cultural one."},
    {"word": "HARMONY", "hint": "The combination of simultaneously sounded musical notes to produce a pleasing effect."},
    {"word": "KINGDOM", "hint": "A country, state, or territory ruled by a king or queen."},
    {"word": "PARADISE", "hint": "An ideal or idyllic place or state of supreme happiness."},
    {"word": "WONDERFUL", "hint": "Inspiring delight, pleasure, or admiration; extremely good."},
    {"word": "MARATHON", "hint": "A long-distance running race, strictly one of 26 miles."},
    {"word": "TREASURE", "hint": "A quantity of precious metals, gems, or other valuable objects."},
    {"word": "SATELLITE", "hint": "An artificial body placed in orbit round the earth or another planet."}
]

# Shared Global State untuk penjejakan Central Administrator
active_players = {}

# ----------------- INTERFACE ADMIN (ADMIN PANEL GRAPHICS) -----------------
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🚨 TOURNAMENT LIVE ADMIN PANEL</title>
    <style>
        body { background-color: #0D0E15; color: #F8F8F2; font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .grid { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .box { background: #1E1E2E; border: 2px solid #00F5D4; padding: 20px; border-radius: 8px; flex: 1; min-width: 350px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .box.leaderboard { border-color: #FF007F; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; border: 1px solid #252538; text-align: center; background: #11111B; }
        th { background: #252538; color: #FFFF00; font-weight: bold; }
        .btn-reset { background-color: #FF477E; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: 0.2s; }
        .btn-reset:hover { background-color: #FF007F; transform: scale(1.05); }
    </style>
    <script>
        async function refreshAdminDashboard() {
            try {
                let res = await fetch('/admin/data');
                let data = await res.json();
                
                let activeRows = `<tr><th>Game Parameters</th><th>Current Live Status</th></tr>`;
                activeRows += `<tr><td><strong>Current Tournament Word</strong></td><td style="color:#FFFF00; font-size:1.2rem; letter-spacing:2px;">${data.word}</td></tr>`;
                activeRows += `<tr><td><strong>Hint Given</strong></td><td style="color:#00F5D4;">${data.hint}</td></tr>`;
                activeRows += `<tr><td><strong>Match Level</strong></td><td>Level ${data.level}/5</td></tr>`;
                activeRows += `<tr><td><strong>Lobby Global Lives</strong></td><td style="color:#FF477E; font-weight:bold;">❤️ ${data.lives}/6</td></tr>`;
                activeRows += `<tr><td><strong>Match Finished Status</strong></td><td>${data.gameover}</td></tr>`;
                document.getElementById('active-table').innerHTML = activeRows;

                let scoreRows = `<tr><th>Rank</th><th>Player Name</th><th>Final Status</th><th>Final Time Record</th></tr>`;
                if(!data.leaderboard || data.leaderboard.length === 0) {
                    scoreRows += `<tr><td colspan="4" style="color:#A4A4C1;">No rankings generated yet. Scoreboard is clean.</td></tr>`;
                } else {
                    data.leaderboard.forEach(l => {
                        let statusColor = l.status === "Playing" ? "#00F5D4" : "#FF477E";
                        scoreRows += `<tr>
                            <td style="color:#FFFF00;">${l.rank}</td>
                            <td style="font-weight:bold; color: #00E5FF;">${l.name}</td>
                            <td><span style="background:${statusColor}; color:#1E1E2E; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:0.85rem;">${l.status}</span></td>
                            <td style="color:#00F5D4;"><strong>${l.time}</strong></td>
                        </tr>`;
                    });
                }
                document.getElementById('score-table').innerHTML = scoreRows;
            } catch(e){}
        }

        async function triggerScoreboardReset() {
            if(confirm("Adakah anda pasti mahu set semula (RESET) keseluruhan papan markah kejohanan ini?")) {
                let res = await fetch('/admin/reset', { method: 'POST' });
                let result = await res.json();
                if(result.status === "success") {
                    alert("Papan markah telah dibersihkan secara total!");
                    refreshAdminDashboard();
                }
            }
        }
        setInterval(refreshAdminDashboard, 1500); // Polling automatik setiap 1.5 saat
    </script>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <div style="text-align: left;">
                <h1 style="color: #00F5D4; margin: 0;">🚨 ITT440 CENTRAL NETWORK MONITOR</h1>
                <p style="color: #A4A4C1; margin: 5px 0 0 0;">Connected to Native Socket Architecture on Server Node (`192.168.50.10`)</p>
            </div>
            <button class="btn-reset" onclick="triggerScoreboardReset()">🔄 RESET SCOREBOARD</button>
        </div>
        
        <div class="grid">
            <div class="box">
                <h3 style="margin-top:0; color:#00F5D4;">📡 CENTRAL SOCKET STATE VARIABLES</h3>
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
@app.route('/admin')
def admin_dashboard():
    return render_template_string(ADMIN_TEMPLATE)

# ----------------- LOGIK RESET PENTADBIRAN -----------------
@app.route('/admin/reset', methods=['POST'])
def reset_scoreboard():
    global active_players
    active_players.clear()
    try:
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Menghubungkan ke server lokal/VM untuk membersihkan state server soket
        temp_sock.connect(('192.168.50.10', 8080))  # Tukar ke 127.0.0.1 jika buat ujian lokal 1 laptop
        send_msg(temp_sock, "RESET_SCORES")
        temp_sock.close()
    except Exception:
        pass
    return jsonify({"status": "success", "message": "Leaderboard flushed successfully"})

# ----------------- LOGIK PEMBENTANGAN / DATA SYNC KLIEN -----------------
@app.route('/guess_letter', methods=['POST'])
def guess_letter():
    req = request.get_json() or {}
    char = req.get('letter', '').upper()
    pid = session.get("player_id")

    secret = session.get("secret_word", "")
    revealed = session.get("revealed_word", [])

    if char in secret:
        for i, l in enumerate(secret):
            if l == char and revealed[i] == "_":
                revealed[i] = char
    else:
        session["lives"] = session.get("lives", 6) - 1

    session["revealed_word"] = revealed
    if pid in active_players:
        active_players[pid]["revealed_word"] = revealed
        active_players[pid]["lives"] = session["lives"]

    if "_" not in revealed:
        if session.get("current_level", 0) + 1 >= len(master_words_pool):
            session["is_game_over"] = True
            if pid in active_players:
                active_players[pid]["is_game_over"] = True

    return jsonify({"status": "success"})

@app.route('/admin/data')
def get_admin_data():
    try:
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.settimeout(0.5) # Cegah web freeze jika server offline
        temp_sock.connect(('192.168.50.10', 8080))  # Tukar ke 127.0.0.1 jika buat ujian lokal 1 laptop
        send_msg(temp_sock, "JOIN:WEB_ADMIN_MONITOR")
        payload = recv_msg(temp_sock)
        temp_sock.close()

        if not payload:
            return jsonify({"word": "OFFLINE", "hint": "OFFLINE", "lives": 0, "level": 0, "gameover": "UNKNOWN", "leaderboard": []})

        tokens = payload.split("|")
        d = {}
        for t in tokens:
            if ":" in t:
                k, v = t.split(":", 1)
                d[k] = v

        leaderboard_data = []
        if d.get("RANKINGS") and d["RANKINGS"] != "IN_PROGRESS":
            rows = d["RANKINGS"].split(";")
            for r in rows:
                tokens_row = r.split(",")
                if len(tokens_row) == 8:
                    leaderboard_data.append({
                        "rank": tokens_row[0], 
                        "name": tokens_row[1],
                        "status": "Lost" if int(tokens_row[7]) < 100 else "Won", 
                        "time": f"{tokens_row[7]}.0s"
                    })

        return jsonify({
            "word": d.get("WORD", "---"),
            "hint": d.get("HINT", "---"),
            "lives": d.get("LIVES", "6"),
            "level": d.get("LEVEL", "1"),
            "gameover": d.get("GAMEOVER", "NO"),
            "leaderboard": leaderboard_data
        })
    except Exception:
        # Menampilkan paparan bersedia sekiranya server soket belum dihidupkan
        return jsonify({
            "word": "STANDBY", "hint": "Waiting for server.py network link...", "lives": 6, "level": 1, "gameover": "NO", "leaderboard": []
        })

if __name__ == '__main__':
    # Ditetapkan ke port 5000 agar serasi dengan konfigurasi hibrid asal anda
    app.run(host='0.0.0.0', port=5000, debug=True)