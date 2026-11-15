import csv
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
from tone_dictionary import TONE_DICTIONARY

# CSV File paths
USERS_CSV = "users.csv"
TRANSITIONS_CSV = "word_transitions.csv"
LOGS_CSV = "user_logs.csv"

class SmartTextApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Text Assistant (CSV Storage)")
        self.root.geometry("800x650")

        self.current_user = None
        self.target_tone = {}
        self.predicted_word = ""
        self.is_completing_word = False
        self.last_saved_content = ""

        # CSV Storage Initialization
        self.init_csv_files()

        # Markov Training using CSV
        row_count = 0
        with open(TRANSITIONS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                row_count += 1
        if row_count <= 1:
            self.train_markov_corpus("corpus.txt")

        # Exit Safety Guard
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Build UI Container
        self.container = tk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Show Initial Screen
        self.show_auth_screen()


    # CSV DATA INITIALIZATION

    def init_csv_files(self):
        if not os.path.exists(USERS_CSV):
            with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "password"])

        if not os.path.exists(TRANSITIONS_CSV):
            with open(TRANSITIONS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["current_word", "next_word", "corpus_freq", "user_freq"])

        if not os.path.exists(LOGS_CSV):
            with open(LOGS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["username", "filename", "word_count", "log_time"]
                )


    # MARKOV CHAIN TRAINING WITH CSV

    def train_markov_corpus(self, filepath):
        if not os.path.exists(filepath):
            default_text = "Hi, how are you? Good morning! Nice to meet you."
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(default_text)

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        self.train_markov_text(text, source="corpus")

    def train_markov_text(self, text, source="user"):
        words = []
        for w in text.lower().split():
            cleaned_word = w.strip(".,!?;:")
            if cleaned_word:
                words.append(cleaned_word)

        if len(words) < 2:
            return

        transitions = {}
        if os.path.exists(TRANSITIONS_CSV):
            with open(TRANSITIONS_CSV, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) == 4:
                        transitions[(row[0], row[1])] = [int(row[2]), int(row[3])]

        for i in range(len(words) - 1):
            pair = (words[i], words[i + 1])
            if pair not in transitions:
                transitions[pair] = [0, 0]

            if source == "corpus":
                transitions[pair][0] += 1
            else:
                transitions[pair][1] += 1

        with open(TRANSITIONS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["current_word", "next_word", "corpus_freq", "user_freq"])
            for (curr_w, next_w), (c_freq, u_freq) in transitions.items():
                writer.writerow([curr_w, next_w, c_freq, u_freq])

    # AUTHENTICATION SCREEN

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_auth_screen(self):
        self.clear_container()

        frame = tk.Frame(self.container, padx=30, pady=30)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            frame, text="Smart Text Assistant", font=("Arial", 18, "bold")
        ).pack(pady=10)

        tk.Label(
            frame,
            text="Please Sign In or Register (CSV Backend)",
            font=("Arial", 10),
        ).pack(pady=(0, 20))

        tk.Label(frame, text="Username:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        self.entry_username = tk.Entry(frame, width=30, font=("Arial", 11))
        self.entry_username.pack(pady=(0, 10))

        tk.Label(frame, text="Password:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        self.entry_password = tk.Entry(
            frame, width=30, font=("Arial", 11), show="*"
        )
        self.entry_password.pack(pady=(0, 20))

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame,
            text="Log In",
            width=12,
            highlightbackground="#4CAF50",#green
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.handle_login,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Sign Up",
            width=12,
            highlightbackground="#2196F3",#blue
            fg="black",
            font=("Arial", 10, "bold"),
            command=self.handle_signup,
        ).pack(side=tk.RIGHT, padx=5)

    def handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Input Error", "Username and Password cannot be empty."
            )
            return

        authenticated = False
        with open(USERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[0] == username and row[1] == password:
                    authenticated = True
                    break

        if authenticated:
            self.current_user = username
            self.last_saved_content = ""
            self.show_tone_selection_screen()
        else:
            messagebox.showerror("Auth Error", "Invalid Username or Password.")

    def handle_signup(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Input Error", "Username and Password cannot be empty."
            )
            return

        # Check if user exists
        user_exists = False
        with open(USERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and row[0] == username:
                    user_exists = True
                    break

        if user_exists:
            messagebox.showerror(
                "Signup Error", "Username already exists. Try logging in."
            )
            return

        # Append new user to users.csv
        with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([username, password])

        # Create folder
        user_dir = os.path.join("user_data", username)
        os.makedirs(user_dir, exist_ok=True)

        messagebox.showinfo(
            "Success", "Account created successfully! You can now log in."
        )


    # TONE SELECTION

    def show_tone_selection_screen(self):
        self.clear_container()

        frame = tk.Frame(self.container, padx=30, pady=20)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            frame,
            text=f"Welcome, {self.current_user}!",
            font=("Arial", 16, "bold"),
            fg="#333",
        ).pack(pady=5)
        tk.Label(
            frame,
            text="Configure your target writing parameters below:",
            font=("Arial", 10),
        ).pack(pady=(0, 20))

        # Emotional
        tk.Label(
            frame, text="1. Emotional Tone:", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.combo_emotional = ttk.Combobox(
            frame,
            state="readonly",
            width=35,
            values=[
                "Joy/Happiness",
                "Anger",
                "Sadness",
                "Fear/Anxiety",
                "Disgust",
                "Surprise",
            ],
        )
        self.combo_emotional.set("Joy/Happiness")
        self.combo_emotional.pack(pady=(0, 15))

        # Behavioral/Social
        tk.Label(
            frame,
            text="2. Behavioral / Social Tone:",
            font=("Arial", 10, "bold"),
        ).pack(anchor="w")
        self.combo_behavioral = ttk.Combobox(
            frame,
            state="readonly",
            width=35,
            values=["Analytical", "Confident", "Tentative", "Respectful/Polite"],
        )
        self.combo_behavioral.set("Analytical")
        self.combo_behavioral.pack(pady=(0, 15))

        # 3. Intentional
        tk.Label(
            frame, text="3. Intentional Tone:", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.combo_intentional = ttk.Combobox(
            frame,
            state="readonly",
            width=35,
            values=["Urgent", "Casual/Conversational", "Formal"],
        )
        self.combo_intentional.set("Formal")
        self.combo_intentional.pack(pady=(0, 20))

        tk.Button(
            frame,
            text="Proceed to Editor ->",
            font=("Arial", 11, "bold"),
            highlightbackground="#FF9800",#orange
            fg="black",
            width=25,
            command=self.save_tone_and_open_editor,
        ).pack()

    def save_tone_and_open_editor(self):
        self.target_tone = {
            "emotional": self.combo_emotional.get(),
            "behavioral": self.combo_behavioral.get(),
            "intentional": self.combo_intentional.get(),
        }
        self.show_main_editor_screen()


    # TEXT EDITOR, PREDICTION

    def show_main_editor_screen(self):
        self.clear_container()

        info_frame = tk.Frame(self.container, bg="#eceff1", padx=10, pady=8)#light grey
        info_frame.pack(fill=tk.X)

        tone_str = f"Target Tone: [{self.target_tone['emotional']} | {self.target_tone['behavioral']} | {self.target_tone['intentional']}]"
        tk.Label(
            info_frame,
            text=f"User: {self.current_user}",
            font=("Arial", 10, "bold"),
            bg="#eceff1",#light grey
        ).pack(side=tk.LEFT)
        tk.Label(
            info_frame,
            text=tone_str,
            font=("Arial", 9, "italic"),
            bg="#eceff1",#light grey
            fg="#37474f",#dark grey
        ).pack(side=tk.RIGHT)

        # Editor Area
        edit_frame = tk.Frame(self.container, padx=10, pady=10)
        edit_frame.pack(fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(
            edit_frame, wrap=tk.WORD, font=("Consolas", 12), undo=True
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Keyboard Bindings
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<Tab>", self.on_tab_press)

        # Ghost Word Area
        self.ghost_label = tk.Label(
            self.container,
            text="Ghost Prediction: None",
            font=("Arial", 10, "bold"),
            fg="gray",
            anchor="w",
            padx=10,
        )
        self.ghost_label.pack(fill=tk.X)

        # Toolbar Buttons
        btn_bar = tk.Frame(self.container, padx=10, pady=10, bg="#f5f5f5")#light grey
        btn_bar.pack(fill=tk.X)

        tk.Button(
            btn_bar,
            text="Analyze Tone Deviation",
            highlightbackground="#9C27B0",#purple
            fg="black",
            font=("Arial", 9, "bold"),
            command=self.analyze_tone_deviation,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_bar,
            text="Save Document",
            highlightbackground="#4CAF50",#green
            fg="black",
            font=("Arial", 9, "bold"),
            command=self.save_file,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_bar,
            text="Load Previous File",
            highlightbackground="#2196F3",#blue
            fg="black",
            font=("Arial", 9, "bold"),
            command=self.load_file,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_bar,
            text="Change Tone Rules",
            highlightbackground="#FF5722",#orange
            fg="black",
            font=("Arial", 9, "bold"),
            command=self.show_tone_selection_screen,
        ).pack(side=tk.RIGHT, padx=5)


    # CSV MARKOV PREDICTION LOOKUP

    #Auto-Complete Word
    def autocomplete_current_word(self, prefix):
        prefix = prefix.lower()
        if not prefix:
            return ""

        USER_WEIGHT = 0.75
        CORPUS_WEIGHT = 0.25

        best_word = ""
        max_score = -1.0

        if os.path.exists(TRANSITIONS_CSV):
            with open(TRANSITIONS_CSV, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) == 4:
                        curr_w, next_w = row[0], row[1]
                        c_freq, u_freq = int(row[2]), int(row[3])
                        score = (u_freq * USER_WEIGHT) + (c_freq * CORPUS_WEIGHT)

                        for candidate in (curr_w, next_w):
                            if candidate.startswith(prefix) and candidate != prefix:
                                if score > max_score:
                                    max_score = score
                                    best_word = candidate

        if not best_word:
            for category, items in TONE_DICTIONARY.items():
                word_list = items.keys() if isinstance(items, dict) else items
                for w in word_list:
                    w_lower = w.lower()
                    if w_lower.startswith(prefix) and w_lower != prefix and " " not in w_lower:
                        return w_lower

        return best_word

    #Next word

    def predict_next_word(self, current_word):
        if not current_word or not os.path.exists(TRANSITIONS_CSV):
            return ""

        USER_WEIGHT = 0.75
        CORPUS_WEIGHT = 0.25

        best_word = ""
        max_score = -1.0

        with open(TRANSITIONS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) == 4:
                    curr = row[0]
                    next_w = row[1]
                    corpus_freq = int(row[2])
                    user_freq = int(row[3])

                    if curr == current_word.lower():
                        score = (user_freq * USER_WEIGHT) + (corpus_freq * CORPUS_WEIGHT)
                        if score > max_score:
                            max_score = score
                            best_word = next_w

        return best_word

    def on_key_release(self, event):
        if event.keysym in (
            "Tab",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
        ):
            return

        raw_content = self.text_area.get("1.0", "insert")
        words = raw_content.split()

        if not words:
            self.predicted_word = ""
            self.is_completing_word = False
            self.ghost_label.config(text="Ghost Prediction: None", fg="gray")
            return

        last_word = words[-1].strip(".,!?;:")

        if raw_content and not raw_content[-1].isspace() and len(last_word) >= 2:
            self.predicted_word = self.autocomplete_current_word(last_word)
            self.is_completing_word = True
            mode_label = "Autocomplete"
        else:
            self.predicted_word = self.predict_next_word(last_word)
            self.is_completing_word = False
            mode_label = "Next Word"

        if self.predicted_word:
            self.ghost_label.config(
                text=f"{mode_label}: '{self.predicted_word}'  [ Press TAB to accept ]",
                fg="#1E88E5",
            )
        else:
            self.ghost_label.config(text="Ghost Prediction: None", fg="gray")

    def on_tab_press(self, event):
        if self.predicted_word:
            raw_content = self.text_area.get("1.0", "insert")

            if self.is_completing_word:
                last_space_idx = raw_content.rfind(" ")
                last_newline_idx = raw_content.rfind("\n")
                split_idx = max(last_space_idx, last_newline_idx)

                prefix_text = raw_content[: split_idx + 1]
                new_content = f"{prefix_text}{self.predicted_word} "

                self.text_area.delete("1.0", "insert")
                self.text_area.insert("1.0", new_content)
            else:
                if raw_content and not raw_content.endswith(" "):
                    to_insert = f" {self.predicted_word} "
                else:
                    to_insert = f"{self.predicted_word} "
                self.text_area.insert("insert", to_insert)

            accepted_word = self.predicted_word
            self.predicted_word = ""
            self.is_completing_word = False

            next_pred = self.predict_next_word(accepted_word)
            if next_pred:
                self.predicted_word = next_pred
                self.ghost_label.config(
                    text=f"Next Word: '{self.predicted_word}'  [ Press TAB to accept ]",
                    fg="#1E88E5",
                )
            else:
                self.ghost_label.config(text="Ghost Prediction: None", fg="gray")

            return "break"


    # SENTIMENT, TONE ANALYSIS

    def analyze_tone_deviation(self):
        text = self.text_area.get("1.0", tk.END).lower()

        words = []
        for w in text.split():
            cleaned_word = w.strip(".,!?;:")
            if cleaned_word:
                words.append(cleaned_word)

        if not words:
            messagebox.showinfo(
                "Analysis Result", "Editor is empty. Write text before analyzing."
            )
            return

        target_emo = self.target_tone.get("emotional")
        target_intent = self.target_tone.get("intentional")

        emo_words = TONE_DICTIONARY.get(target_emo, [])
        emo_hits = []
        for w in words:
            if w in emo_words:
                emo_hits.append(w)

        formal_replacements = TONE_DICTIONARY.get("Formal", {})
        casual_found = []
        for w in words:
            if w in formal_replacements:
                casual_found.append(w)

        emo_score = (len(emo_hits) / len(words)) * 100

        report = f"--- Tone Deviation & Analysis Report ---\n\n"
        report += f"Total Words Analysed: {len(words)}\n"
        report += f"Target Emotional Tone: {target_emo}\n"
        report += (
            f"Emotional Words Detected ({len(emo_hits)}): "
            f"{', '.join(emo_hits) if emo_hits else 'None'}\n"
        )
        report += f"Emotional Match: {emo_score:.1f}%\n\n"

        if target_intent == "Formal":
            report += f"Tone Target: Formal\n"
            report += (
                f"Casual / Informal Terms Detected: {len(casual_found)}\n"
            )
            if casual_found:
                report += "\nSuggested Formal Replacements:\n"
                for word in set(casual_found):
                    report += (
                        f"  • '{word}'  -->  '{formal_replacements[word]}'\n"
                    )
            else:
                report += "Excellent! Formal tone.\n"

        messagebox.showinfo("Tone Deviation", report)


    # FILE HANDLING & CSV LOGGING ACTIONS

    def save_file(self):
        filename = simpledialog.askstring(
            "Save Document", "Enter filename (without extension):"
        )
        if not filename:
            return

        content = self.text_area.get("1.0", tk.END)
        word_count = len(content.split())

        # Save document inside user folder
        user_dir = os.path.join("user_data", self.current_user)
        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, f"{filename}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        old_text = self.last_saved_content.strip()
        new_text = content.strip()

        if old_text and new_text.startswith(old_text):
            old_words = old_text.split()
            bridge_word = old_words[-1] if old_words else ""
            added_part = new_text[len(old_text):].strip()

            if added_part:
                text_to_train = f"{bridge_word} {added_part}".strip()
                self.train_markov_text(text_to_train)

        elif new_text != old_text:
            self.train_markov_text(new_text)

        self.last_saved_content = content

        # Save log entry
        with open(LOGS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    self.current_user,
                    f"{filename}.txt",
                    word_count,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        messagebox.showinfo(
            "Save Success",
            f"File saved successfully to:\n{filepath}\n\nLogged save event to {LOGS_CSV}.",
        )

    def load_file(self):
        user_dir = os.path.join("user_data", self.current_user)
        if not os.path.exists(user_dir) or not os.listdir(user_dir):
            messagebox.showinfo(
                "Load Document", "No saved documents found in your folder."
            )
            return

        files = []
        for filename in os.listdir(user_dir):
            if filename.endswith(".txt"):
                files.append(filename)

        if not files:
            messagebox.showinfo(
                "Load Document", "No .txt files available to load."
            )
            return

        select_win = tk.Toplevel(self.root)
        select_win.title("Select Document to Load")
        select_win.geometry("300x300")

        tk.Label(
            select_win,
            text="Select a file from your folder:",
            font=("Arial", 10, "bold"),
        ).pack(pady=10)
        listbox = tk.Listbox(select_win, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for file in files:
            listbox.insert(tk.END, file)

        def open_selected():
            selection = listbox.curselection()
            if selection:
                filename = listbox.get(selection[0])
                filepath = os.path.join(user_dir, filename)

                with open(filepath, "r", encoding="utf-8") as f:
                    data = f.read()

                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", data)
                self.last_saved_content = data
                select_win.destroy()
                messagebox.showinfo(
                    "File Loaded", f"Successfully loaded '{filename}'."
                )

        tk.Button(
            select_win,
            text="Open File",
            highlightbackground="#2196F3",
            fg="black",
            font=("Arial", 10, "bold"),
            command=open_selected,
        ).pack(pady=10)

    # EXIT GUARD
    def on_closing(self):
        if hasattr(self, "text_area"):
            current_content = self.text_area.get("1.0", tk.END)
            if current_content.strip() != self.last_saved_content.strip():
                response = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved changes. Would you like to save before exiting?",
                )
                if response is True:
                    self.save_file()
                elif response is None:
                    return

        self.root.destroy()

# MAIN APPLICATION ENTRY POINT
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartTextApp(root)
    root.mainloop()