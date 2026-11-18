import os
from datetime import datetime
import customtkinter as ctk

FONT_FAMILY = "Segoe UI"


class HistoryView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.active_history_file = ""
        self.build_ui()

    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        theme = self.app.get_theme_colors()

        container = ctk.CTkFrame(self, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        container.pack(fill="both", expand=True, padx=30, pady=25)

        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(18, 10))

        ctk.CTkLabel(
            header_frame, text="GENERATION HISTORY & EXPORTS", font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color=theme["ACCENT_PURPLE"]
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, text="🔄 Refresh Folder", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent", border_color=theme["BORDER"], border_width=1, hover_color=theme["CARD"],
            text_color=theme["TEXT_PRIMARY"], width=110, height=28, command=self.refresh_list
        ).pack(side="right")

        self.history_list = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.history_list.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.refresh_list()

    def refresh_list(self):
        theme = self.app.get_theme_colors()

        for widget in self.history_list.winfo_children():
            widget.destroy()

        files = self.app.get_all_exported_files()

        if not files:
            ctk.CTkLabel(
                self.history_list, text="No generated audio files found in the export location.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=theme["TEXT_SECONDARY"]
            ).pack(pady=30)
            return

        for file_path in files:
            filename = os.path.basename(file_path)

            try:
                mod_time = os.path.getmtime(file_path)
                dt_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d  %I:%M:%S %p")
            except Exception:
                dt_str = "Unknown Date"

            item_frame = ctk.CTkFrame(self.history_list, fg_color=theme["CARD"], corner_radius=8, border_color=theme["BORDER"], border_width=1)
            item_frame.pack(fill="x", pady=5, padx=5)

            left_box = ctk.CTkFrame(item_frame, fg_color="transparent")
            left_box.pack(side="left", padx=15, pady=10)

            ctk.CTkLabel(left_box, text=filename, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color=theme["TEXT_PRIMARY"]).pack(anchor="w")
            ctk.CTkLabel(left_box, text=f"📅 Created: {dt_str}", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=theme["TEXT_SECONDARY"]).pack(anchor="w", pady=(2, 0))

            btn_box = ctk.CTkFrame(item_frame, fg_color="transparent")
            btn_box.pack(side="right", padx=15, pady=10)

            # Wrapped commands in lambda functions to defer evaluation
            play_btn = ctk.CTkButton(
                btn_box, text="▶ Play", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                width=65, height=28, fg_color=theme["ACCENT_CYAN"], text_color="#000000",
                command=lambda f=file_path: self.play_history_file(f)
            )
            play_btn.pack(side="left", padx=3)

            pause_btn = ctk.CTkButton(
                btn_box, text="⏸ Pause", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                width=65, height=28, fg_color=theme["BORDER"], text_color=theme["TEXT_PRIMARY"],
                command=lambda: self.app.pause_audio()
            )
            pause_btn.pack(side="left", padx=3)

            stop_btn = ctk.CTkButton(
                btn_box, text="⏹ Stop", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                width=65, height=28, fg_color=theme["BORDER"], text_color=theme["TEXT_PRIMARY"],
                command=lambda: self.app.stop_audio()
            )
            stop_btn.pack(side="left", padx=3)

    def play_history_file(self, file_path):
        self.active_history_file = file_path
        self.app.load_and_play_history(file_path)

    def refresh(self):
        self.build_ui()