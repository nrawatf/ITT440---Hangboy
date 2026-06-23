import socket
import threading
from network_utils import send_msg, recv_msg

# 🎯 Official Tournament Match Progression Pools
words_pool = [
    {"word": "CHALLENGE", "hint": "A task or situation that tests someone's abilities."},
    {"word": "JOURNEY", "hint": "An act of traveling from one place to another."},
    {"word": "HORIZON", "hint": "The line at which the earth's surface and the sky appear to meet."},
    {"word": "MYSTERY", "hint": "Something that is difficult or impossible to understand or explain."},
    {"word": "VICTORY", "hint": "An act of defeating an enemy or opponent."}
]

clients = {}       # socket -> player name
scores = {}        # player name -> list of 5 integers [lvl1, lvl2, lvl3, lvl4, lvl5]
state_lock = threading.Lock()

game_state = {
    "current_level": 0,
    "secret_word": "",
    "hint": "",
    "revealed_word": [],
    "global_lives": 6,
    "is_game_over": False
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

load_level()

def generate_sync_payload(system_alert=""):
    with state_lock:
        rankings_str = ""
        if game_state["is_game_over"]:
            player_summaries = []
            for name, lvl_points in scores.items():
                total = sum(lvl_points)
                player_summaries.append({
                    "name": name,
                    "total": total,
                    "lvls": lvl_points
                })
            
            # 🔥 SORT MULTIPLAYER COMPETITORS BY GRAND TOTAL (HIGHEST TO LOWEST)
            player_summaries.sort(key=lambda x: x["total"], reverse=True)
            
            summary_lines = []
            for rank, player in enumerate(player_summaries, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
                rank_display = f"{medal} #{rank}" if medal else f"#{rank}"
                row_data = f"{rank_display},{player['name']},{player['lvls'][0]},{player['lvls'][1]},{player['lvls'][2]},{player['lvls'][3]},{player['lvls'][4]},{player['total']}"
                summary_lines.append(row_data)
                
            rankings_str = ";".join(summary_lines)
        else:
            rankings_str = "IN_PROGRESS"

        return (
            f"WORD:{' '.join(game_state['revealed_word'])}|"
            f"LIVES:{game_state['global_lives']}|"
            f"HINT:{game_state['hint']}|"
            f"RANKINGS:{rankings_str}|"
            f"MSG:{system_alert}|"
            f"LEVEL:{game_state['current_level'] + 1}|"
            f"GAMEOVER:{'YES' if game_state['is_game_over'] else 'NO'}"
        )

def broadcast_to_all(payload):
    for client_sock in list(clients.keys()):
        send_msg(client_sock, payload)

def handle_player_session(client_socket):
    global game_state
    player_name = "ANONYMOUS"
    
    init_msg = recv_msg(client_socket)
    if init_msg and init_msg.startswith("JOIN:"):
        player_name = init_msg.split(":", 1)[1].strip().upper()
        
    with state_lock:
        clients[client_socket] = player_name
        if player_name not in scores:
            scores[player_name] = [0, 0, 0, 0, 0]

    print(f"📡 [CONNECTED] Player '{player_name}' synchronized successfully.")
    send_msg(client_socket, generate_sync_payload(f"👋 Welcome {player_name}! Match starting shortly."))
    broadcast_to_all(generate_sync_payload(f"📢 Player '{player_name}' synchronized into lobby."))

    while True:
        data = recv_msg(client_socket)
        if not data:
            break

        system_msg = ""
        current_lvl_idx = game_state["current_level"]
        
        if data.startswith("GUESS:"):
            char = data.split(":", 1)[1].upper()
            
            with state_lock:
                if game_state["global_lives"] > 0 and "_" in game_state["revealed_word"]:
                    if char in game_state["secret_word"]:
                        correct_hit = False
                        for idx, letter in enumerate(game_state["secret_word"]):
                            if letter == char and game_state["revealed_word"][idx] == "_":
                                game_state["revealed_word"][idx] = char
                                correct_hit = True
                        if correct_hit:
                            scores[player_name][current_lvl_idx] += 15
                            system_msg = f"🎯 {player_name} solved '{char}'! (+15 pts)"
                        else:
                            system_msg = f"ℹ️ Character '{char}' was already solved."
                    else:
                        game_state["global_lives"] -= 1
                        system_msg = f"❌ {player_name} guessed '{char}' incorrectly! (-1 Life)"

                    if "_" not in game_state["revealed_word"]:
                        if game_state["current_level"] + 1 >= len(words_pool):
                            game_state["is_game_over"] = True
                            scores[player_name][current_lvl_idx] += 50
                            system_msg = "🏁 TOURNAMENT COMPLETED! Game Over. Grand ranking table generated."
                        else:
                            scores[player_name][current_lvl_idx] += 50
                            system_msg = f"🎉 LEVEL {current_lvl_idx+1} CLEARED! (+50 bonus points to {player_name}). Click 'Next Level'."
                    elif game_state["global_lives"] <= 0:
                        game_state["is_game_over"] = True
                        system_msg = f"💀 MATCH FAILED! No lives left. Target word was: '{game_state['secret_word']}'."

            broadcast_to_all(generate_sync_payload(system_msg))

        elif data == "REQUEST_NEXT":
            with state_lock:
                if game_state["current_level"] + 1 < len(words_pool) and "_" not in game_state["revealed_word"]:
                    game_state["current_level"] += 1
                    load_level()
                    system_msg = f"🔄 {player_name} moved the team forward to Level {game_state['current_level'] + 1}!"
            broadcast_to_all(generate_sync_payload(system_msg))

    print(f"🛑 [DISCONNECTED] Player '{player_name}' logged off.")
    with state_lock:
        if client_socket in clients:
            del clients[client_socket]
    broadcast_to_all(generate_sync_payload(f"🚨 Connection lost with player '{player_name}'."))
    client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8080))
    server.listen()
    print("🚀 [Hangboy Server] Multiplayer lobby active on port 8080...")

    while True:
        client_sock, _ = server.accept()
        threading.Thread(target=handle_player_session, args=(client_sock,), daemon=True).start()

if __name__ == '__main__':
    main()