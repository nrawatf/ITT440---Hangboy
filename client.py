import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from network_utils import send_msg, recv_msg

class ScoreboardWindow:
    """Creates a high-contrast grid table displaying final competitive leaderboard ranks."""
    def __init__(self, parent_root, rankings_data):
        self.win = tk.Toplevel(parent_root)
        self.win.title("🏆 Leaderboard Tally")
        self.win.geometry("750x450")
        self.win.configure(bg="#11111B")
        
        self.win.transient(parent_root)
        self.win.grab_set()
        
        title = tk.Label(self.win, text="🏆 TOURNAMENT FINAL RANKINGS", font=("Segoe UI", 16, "bold"), fg="#FFFF00", bg="#11111B")
        title.pack(pady=15)
        
        # Configure Table Matrix Styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#252538", foreground="#F8F8F2", fieldbackground="#252538", rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#1E1E2E", foreground="#00F5D4", font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("Treeview", background=[('selected', '#FF007F')])

        # Build Table Grid Structure
        columns = ("rank", "name", "l1", "l2", "l3", "l4", "l5", "total")
        self.tree = ttk.Treeview(self.win, columns=columns, show="headings", height=8)
        
        headers = {
            "rank": "Rank", "name": "Player Name", "l1": "Lvl 1",
            "l2": "Lvl 2", "l3": "Lvl 3", "l4": "Lvl 4", "l5": "Lvl 5", "total": "Grand Total"
        }
        widths = {"rank": 80, "name": 160, "l1": 65, "l2": 65, "l3": 65, "l4": 65, "l5": 65, "total": 120}
        
        for col, text in headers.items():
            self.tree.heading(col, text=text, anchor="center")
            self.tree.column(col, width=widths[col], anchor="center")

        # Parse Data and Add Rows
        rows = rankings_data.split(";")
        for r in rows:
            if r.strip():
                tokens = r.split(",")
                if len(tokens) == 8:
                    self.tree.insert("", "end", values=tokens)

        self.tree.pack(fill="both", expand=True, padx=25, pady=10)
        
        close_btn = tk.Button(self.win, text="DISMISS SCOREBOARD", font=("Segoe UI", 11, "bold"), bg="#FF007F", fg="white", command=self.win.destroy, padx=25, pady=5)
        close_btn.pack(pady=15)

class HangboyClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multiplayer Hangboy Player Station")
        self.root.geometry("950x600")
        self.root.configure(bg="#1E1E2E")
        
        self.sock = None
        self.my_nickname = ""
        self.scoreboard_opened = False
        
        self.create_auth_screen()
        self.create_dashboard_screen()
        
        self.auth_frame.pack(fill="both", expand=True)

    def create_auth_screen(self):
        self.auth_frame = tk.Frame(self.root, bg="#1E1E2E")
        
        title_lbl = tk.Label(self.auth_frame, text="🎯 MULTIPLAYER HANGBOY LOBBY", font=("Segoe UI", 24, "bold"), fg="#FF007F", bg="#1E1E2E")
        title_lbl.pack(pady=40)
        
        card = tk.Frame(self.auth_frame, bg="#252538", bd=2, relief="groove", padx=30, pady=30)
        card.pack(pady=10)
        
        name_lbl = tk.Label(card, text="Enter Your Player Nickname:", font=("Segoe UI", 14), fg="#F8F8F2", bg="#252538")
        name_lbl.pack(pady=10)
        
        self.name_entry = tk.Entry(card, font=("Consolas", 16), width=20, justify="center", bg="#11111B", fg="#FFFF00", insertbackground="white")
        self.name_entry.pack(pady=10)
        self.name_entry.focus_set()
        
        join_btn = tk.Button(card, text="LAUNCH MULTIPLAYER GAME MATCH", font=("Segoe UI", 12, "bold"), bg="#00F5D4", fg="#1E1E2E", activebackground="#00D2B4", width=30, height=2, command=self.attempt_connection)
        join_btn.pack(pady=20)

    def create_dashboard_screen(self):
        self.main_frame = tk.Frame(self.root, bg="#1E1E2E")
        
        top_bar = tk.Frame(self.main_frame, bg="#252538", height=50)
        top_bar.pack(fill="x", side="top", pady=5)
        
        self.player_lbl = tk.Label(top_bar, text="👤 Player: ---", font=("Segoe UI", 12, "bold"), fg="#00E5FF", bg="#252538", padx=15)
        self.player_lbl.pack(side="left")
        
        self.level_lbl = tk.Label(top_bar, text="Level: 1/5", font=("Segoe UI", 12, "bold"), fg="#FFFF00", bg="#252538", padx=15)
        self.level_lbl.pack(side="right")
        
        self.lives_lbl = tk.Label(top_bar, text="❤️ Lives: 6/6", font=("Segoe UI", 12, "bold"), fg="#FF477E", bg="#252538", padx=15)
        self.lives_lbl.pack(side="right")

        center_split = tk.Frame(self.main_frame, bg="#1E1E2E")
        center_split.pack(fill="both", expand=True, padx=15, pady=5)

        self.canvas_frame = tk.Frame(center_split, bg="#1E1E2E")
        self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        self.hangman_canvas = tk.Canvas(self.canvas_frame, width=220, height=280, bg="#11111B", highlightbackground="#FF007F", highlightthickness=2)
        self.hangman_canvas.pack(pady=10)

        self.game_controls_frame = tk.Frame(center_split, bg="#1E1E2E")
        self.game_controls_frame.pack(side="right", fill="both", expand=True, padx=10)

        hint_card = tk.Frame(self.game_controls_frame, bg="#11111B", bd=1, relief="solid")
        hint_card.pack(fill="x", pady=5)
        tk.Label(hint_card, text="💡 QUESTION HINT", font=("Segoe UI", 9, "bold"), fg="#A4A4C1", bg="#11111B").pack(anchor="w", padx=10, pady=2)
        self.hint_lbl = tk.Label(hint_card, text="Loading parameters...", font=("Segoe UI", 12, "italic"), fg="#00F5D4", bg="#11111B", wraplength=450, justify="left")
        self.hint_lbl.pack(fill="x", padx=15, pady=8)

        word_card = tk.Frame(self.game_controls_frame, bg="#252538", pady=15)
        word_card.pack(fill="x", pady=5)
        self.word_lbl = tk.Label(word_card, text="_ _ _ _ _ _", font=("Courier New", 28, "bold"), fg="#FFFF00", bg="#252538")
        self.word_lbl.pack()

        input_bar = tk.Frame(self.game_controls_frame, bg="#1E1E2E")
        input_bar.pack(pady=10)
        tk.Label(input_bar, text="Guess Letter:", font=("Segoe UI", 11), fg="#F8F8F2", bg="#1E1E2E").pack(side="left", padx=5)
        self.guess_entry = tk.Entry(input_bar, font=("Consolas", 14, "bold"), width=4, justify="center", bg="#11111B", fg="#FF007F", insertbackground="white")
        self.guess_entry.pack(side="left", padx=5)
        self.guess_entry.bind("<Return>", lambda event: self.send_guess())
        
        self.submit_btn = tk.Button(input_bar, text="SUBMIT", font=("Segoe UI", 10, "bold"), bg="#00F5D4", fg="#1E1E2E", command=self.send_guess, width=10)
        self.submit_btn.pack(side="left", padx=5)
        
        self.next_btn = tk.Button(input_bar, text="NEXT LEVEL ➡️", font=("Segoe UI", 10, "bold"), bg="#FF007F", fg="white", command=self.trigger_next_level, width=14)

        log_frame = tk.Frame(self.main_frame, bg="#1E1E2E")
        log_frame.pack(fill="x", side="bottom", padx=25, pady=10)
        tk.Label(log_frame, text="💬 Transmission Logs:", font=("Segoe UI", 10, "bold"), fg="#A4A4C1", bg="#1E1E2E").pack(anchor="w")
        
        self.log_box = tk.Text(log_frame, font=("Consolas", 9), bg="#11111B", fg="#A4A4C1", state="disabled", wrap="word", height=5)
        self.log_box.pack(fill="x")

    def draw_hangman(self, lives):
        self.hangman_canvas.delete("all")
        self.hangman_canvas.create_line(20, 250, 180, 250, fill="#F8F8F2", width=3)
        self.hangman_canvas.create_line(60, 250, 60, 40, fill="#F8F8F2", width=3)
        self.hangman_canvas.create_line(60, 40, 140, 40, fill="#F8F8F2", width=3)
        self.hangman_canvas.create_line(140, 40, 140, 70, fill="#F8F8F2", width=2)

        if lives <= 5: 
            self.hangman_canvas.create_oval(120, 70, 160, 110, outline="#00F5D4", width=3)
        if lives <= 4: 
            self.hangman_canvas.create_line(140, 110, 140, 180, fill="#00F5D4", width=3)
        if lives <= 3: 
            self.hangman_canvas.create_line(140, 130, 110, 150, fill="#00F5D4", width=3)
        if lives <= 2: 
            self.hangman_canvas.create_line(140, 130, 170, 150, fill="#00F5D4", width=3)
        if lives <= 1: 
            self.hangman_canvas.create_line(140, 180, 110, 220, fill="#00F5D4", width=3)
        if lives <= 0: 
            self.hangman_canvas.create_line(140, 180, 170, 220, fill="#FF477E", width=3)
            self.hangman_canvas.create_line(132, 85, 138, 91, fill="#FF477E", width=2)
            self.hangman_canvas.create_line(138, 85, 132, 91, fill="#FF477E", width=2)
            self.hangman_canvas.create_line(142, 85, 148, 91, fill="#FF477E", width=2)
            self.hangman_canvas.create_line(148, 85, 142, 91, fill="#FF477E", width=2)

    def append_log_stream(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f">> {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def attempt_connection(self):
        name_input = self.name_entry.get().strip().upper()
        if not name_input:
            messagebox.showerror("Validation Error", "Nickname entry cannot be empty!")
            return
        
        self.my_nickname = name_input
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('127.0.0.1', 8080))
            send_msg(self.sock, f"JOIN:{self.my_nickname}")
            
            self.auth_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True)
            self.player_lbl.configure(text=f"👤 Player: {self.my_nickname}")
            
            threading.Thread(target=self.receive_broker_updates, daemon=True).start()
            self.guess_entry.focus_set()
        except Exception:
            messagebox.showerror("Connection Timeout", "Failed to locate active matchmaking hub.")

    def receive_broker_updates(self):
        while True:
            payload = recv_msg(self.sock)
            if not payload:
                break
            tokens = payload.split("|")
            data_map = {}
            for t in tokens:
                if ":" in t:
                    k, v = t.split(":", 1)
                    data_map[k] = v
            self.root.after(0, lambda: self.update_gui_components(data_map))
        self.root.after(0, self.handle_graceful_shutdown)

    def update_gui_components(self, d):
        if "WORD" in d: self.word_lbl.configure(text=d["WORD"])
        if "HINT" in d: self.hint_lbl.configure(text=d["HINT"])
        if "LIVES" in d: 
            self.lives_lbl.configure(text=f"❤️ Lives: {d['LIVES']}/6")
            self.draw_hangman(int(d['LIVES']))
        if "LEVEL" in d: self.level_lbl.configure(text=f"Level: {d['LEVEL']}/5")
        
        if "MSG" in d and d["MSG"]:
            self.append_log_stream(d["MSG"])
            
        if "WORD" in d and "_" not in d["WORD"] and d.get("LEVEL") != "5":
            self.next_btn.pack(side="left", padx=5)
        else:
            self.next_btn.pack_forget()
            
        if d.get("GAMEOVER") == "YES":
            self.submit_btn.configure(state="disabled")
            self.guess_entry.configure(state="disabled")
            if not self.scoreboard_opened and "RANKINGS" in d:
                self.scoreboard_opened = True
                ScoreboardWindow(self.root, d["RANKINGS"])

    def send_guess(self):
        char = self.guess_entry.get().strip().upper()
        self.guess_entry.delete(0, tk.END)
        if len(char) == 1 and char.isalpha():
            send_msg(self.sock, f"GUESS:{char}")

    def trigger_next_level(self):
        send_msg(self.sock, "REQUEST_NEXT")

    def handle_graceful_shutdown(self):
        messagebox.showwarning("Network Disconnection", "Connection lost.")
        self.root.quit()

if __name__ == '__main__':
    window = tk.Tk()
    app = HangboyClientGUI(window)
    window.mainloop()