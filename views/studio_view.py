import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

FONT_FAMILY = "Segoe UI"


class StudioView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        theme = self.app.get_theme_colors()

        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=0, column=0, sticky="nsew", padx=30, pady=(15, 15))
        workspace.grid_columnconfigure(0, weight=3)
        workspace.grid_columnconfigure(1, weight=2)
        workspace.grid_rowconfigure(0, weight=1)

        # Left Panel: Text Editor
        editor_frame = ctk.CTkFrame(workspace, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        editor_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        editor_frame.grid_rowconfigure(1, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(editor_frame, fg_color="transparent", height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))

        ctk.CTkLabel(toolbar, text="DOCUMENT TEXT", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=theme["TEXT_SECONDARY"]).pack(side="left")

        self.import_btn = ctk.CTkButton(
            toolbar, text="📁 Import File", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent", border_color=theme["BORDER"], border_width=1, hover_color=theme["CARD"],
            text_color=theme["TEXT_PRIMARY"], width=105, height=28, command=self.browse_file
        )
        self.import_btn.pack(side="right")

        self.text_entry = ctk.CTkTextbox(
            editor_frame, fg_color=theme["CARD"], text_color=theme["TEXT_PRIMARY"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13), wrap="word", corner_radius=8, border_width=0
        )
        self.text_entry.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.text_entry.insert("0.0", "Welcome to the Text To Speech Studio.\n\nStart typing here or import a document to begin generating audio.")

        # Right Panel: Settings Controls
        settings_frame = ctk.CTkFrame(workspace, fg_color="transparent")
        settings_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # Voice Card Header with Refresh Button
        voice_card = ctk.CTkFrame(settings_frame, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        voice_card.pack(fill="x", pady=(0, 12))

        voice_header = ctk.CTkFrame(voice_card, fg_color="transparent")
        voice_header.pack(fill="x", padx=20, pady=(12, 5))

        ctk.CTkLabel(
            voice_header, text="SYSTEM VOICE", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), 
            text_color=theme["TEXT_SECONDARY"]
        ).pack(side="left")

        # 🔄 Voice Refresh Button
        self.refresh_voices_btn = ctk.CTkButton(
            voice_header, text="🔄 Refresh", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            fg_color="transparent", border_color=theme["BORDER"], border_width=1,
            hover_color=theme["CARD"], text_color=theme["ACCENT_CYAN"],
            width=70, height=22, command=lambda: self.app.reload_voices()
        )
        self.refresh_voices_btn.pack(side="right")

        self.voice_var = ctk.StringVar(value="Fetching voices...")
        self.voice_combo = ctk.CTkOptionMenu(
            voice_card, variable=self.voice_var, values=["Fetching voices..."],
            fg_color=theme["CARD"], button_color=theme["CARD"], button_hover_color=theme["BORDER"],
            text_color=theme["TEXT_PRIMARY"], font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self.update_voice_metadata
        )
        self.voice_combo.pack(fill="x", padx=20, pady=(0, 10))

        self.meta_frame = ctk.CTkFrame(voice_card, fg_color="transparent")
        self.meta_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.tag_gender_bg = ctk.CTkFrame(self.meta_frame, fg_color=theme["BORDER"], corner_radius=4)
        self.tag_gender_bg.pack(side="left", padx=(0, 5))
        self.tag_gender = ctk.CTkLabel(self.tag_gender_bg, text="Gender: N/A", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=theme["TEXT_PRIMARY"])
        self.tag_gender.pack(padx=8, pady=2)

        self.tag_lang_bg = ctk.CTkFrame(self.meta_frame, fg_color=theme["BORDER"], corner_radius=4)
        self.tag_lang_bg.pack(side="left", padx=5)
        self.tag_lang = ctk.CTkLabel(self.tag_lang_bg, text="Lang: N/A", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=theme["TEXT_PRIMARY"])
        self.tag_lang.pack(padx=8, pady=2)

        # Audio Parameters Card
        params_card = ctk.CTkFrame(settings_frame, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        params_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(params_card, text="AUDIO PARAMETERS", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=theme["TEXT_SECONDARY"]).pack(anchor="w", padx=20, pady=(15, 8))

        speed_header = ctk.CTkFrame(params_card, fg_color="transparent")
        speed_header.pack(fill="x", padx=20)
        ctk.CTkLabel(speed_header, text="Voice Speed", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=theme["TEXT_PRIMARY"]).pack(side="left")

        saved_speed = self.app.settings.get("speed", 5)
        self.speed_value_label = ctk.CTkLabel(speed_header, text=f"{int(saved_speed)}/10", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=theme["ACCENT_CYAN"])
        self.speed_value_label.pack(side="right")

        self.speed_slider = ctk.CTkSlider(params_card, from_=1, to=10, number_of_steps=9, command=self.update_speed_label, button_color=theme["ACCENT_CYAN"], progress_color=theme["ACCENT_CYAN"])
        self.speed_slider.set(saved_speed)
        self.speed_slider.pack(fill="x", padx=20, pady=(0, 10))

        volume_header = ctk.CTkFrame(params_card, fg_color="transparent")
        volume_header.pack(fill="x", padx=20)
        ctk.CTkLabel(volume_header, text="Volume", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=theme["TEXT_PRIMARY"]).pack(side="left")

        saved_volume = self.app.settings.get("volume", 100)
        self.volume_value_label = ctk.CTkLabel(volume_header, text=f"{int(saved_volume)}%", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=theme["ACCENT_CYAN"])
        self.volume_value_label.pack(side="right")

        self.volume_slider = ctk.CTkSlider(params_card, from_=0, to=100, number_of_steps=100, command=self.update_volume_label, button_color=theme["ACCENT_CYAN"], progress_color=theme["ACCENT_CYAN"])
        self.volume_slider.set(saved_volume)
        self.volume_slider.pack(fill="x", padx=20, pady=(0, 15))

        # Recent Generations Card
        history_card = ctk.CTkFrame(settings_frame, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        history_card.pack(fill="both", expand=True)

        ctk.CTkLabel(history_card, text="RECENT GENERATIONS", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=theme["TEXT_SECONDARY"]).pack(anchor="w", padx=20, pady=(15, 5))

        self.history_list = ctk.CTkScrollableFrame(history_card, fg_color="transparent")
        self.history_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refresh_recent_generations()

        # Bottom Bar
        bottom_bar = ctk.CTkFrame(self, fg_color=theme["SIDEBAR"], corner_radius=0, height=85)
        bottom_bar.grid(row=1, column=0, sticky="sew")
        bottom_bar.grid_columnconfigure(0, weight=1)
        bottom_bar.grid_columnconfigure(1, weight=0)

        center_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="ew", padx=(25, 15), pady=18)
        center_frame.grid_columnconfigure(1, weight=1)

        control_btns = ctk.CTkFrame(center_frame, fg_color="transparent")
        control_btns.grid(row=0, column=0, sticky="w", padx=(0, 15))

        btn_style = {"width": 32, "height": 32, "fg_color": "transparent", "hover_color": theme["CARD"], "text_color": theme["ACCENT_CYAN"], "font": ctk.CTkFont(family=FONT_FAMILY, size=14)}
        
        self.play_btn = ctk.CTkButton(control_btns, text="▶", state="disabled", command=lambda: self.app.play_audio(), **btn_style)
        self.play_btn.pack(side="left")
        self.pause_btn = ctk.CTkButton(control_btns, text="⏸", state="disabled", command=lambda: self.app.pause_audio(), **btn_style)
        self.pause_btn.pack(side="left")
        self.stop_btn = ctk.CTkButton(control_btns, text="⏹", state="disabled", command=lambda: self.app.stop_audio(), **btn_style)
        self.stop_btn.pack(side="left")

        progress_container = ctk.CTkFrame(center_frame, fg_color="transparent")
        progress_container.grid(row=0, column=1, sticky="ew")

        top_p = ctk.CTkFrame(progress_container, fg_color="transparent")
        top_p.pack(fill="x", pady=(0, 2))

        self.status_label = ctk.CTkLabel(top_p, text="Status: Ready", text_color=theme["TEXT_SECONDARY"], font=ctk.CTkFont(family=FONT_FAMILY, size=11))
        self.status_label.pack(side="left")

        self.time_label = ctk.CTkLabel(top_p, text="00:00 / 00:00 (0%)", text_color=theme["TEXT_SECONDARY"], font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"))
        self.time_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(progress_container, height=8, progress_color=theme["ACCENT_CYAN"], fg_color=theme["CARD"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        right_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="e", padx=(15, 25), pady=18)

        self.gen_btn = ctk.CTkButton(
            right_frame, text="⚡ GENERATE", font=ctk.CTkFont(family=FONT_FAMILY, weight="bold", size=12),
            fg_color=theme["CARD"], hover_color=theme["PANEL"], text_color=theme["TEXT_PRIMARY"],
            corner_radius=6, height=36, width=120, border_color=theme["ACCENT_PURPLE"], border_width=1, command=lambda: self.app.generate_preview()
        )
        self.gen_btn.pack(side="left", padx=(0, 10))

        format_bg = ctk.CTkFrame(right_frame, fg_color=theme["CARD"], corner_radius=6, border_color=theme["BORDER"], border_width=1)
        format_bg.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(format_bg, text="FORMAT", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=theme["TEXT_PRIMARY"]).pack(side="left", padx=(10, 2))

        saved_format = self.app.settings.get("format", "mp3")
        self.format_var = ctk.StringVar(value=f".{saved_format}" if not saved_format.startswith(".") else saved_format)

        self.format_combo = ctk.CTkComboBox(
            format_bg, variable=self.format_var, values=[".wav", ".mp3"], width=70, height=36,
            fg_color=theme["CARD"], border_width=0, button_color=theme["CARD"], button_hover_color=theme["PANEL"],
            dropdown_fg_color=theme["PANEL"], text_color=theme["TEXT_PRIMARY"], font=ctk.CTkFont(family=FONT_FAMILY, weight="bold")
        )
        self.format_combo.pack(side="left", padx=(0, 2))

        self.download_btn = ctk.CTkButton(
            right_frame, text="📥 Download", font=ctk.CTkFont(family=FONT_FAMILY, weight="bold", size=12),
            fg_color=theme["ACCENT_CYAN"], hover_color="#33D1B5", text_color="#000000",
            corner_radius=6, height=36, width=110, state="disabled", command=lambda: self.app.download_audio()
        )
        self.download_btn.pack(side="left")

    def refresh_recent_generations(self):
        theme = self.app.get_theme_colors()

        for widget in self.history_list.winfo_children():
            widget.destroy()

        recent_files = self.app.recent_generations[:5]

        if not recent_files:
            ctk.CTkLabel(
                self.history_list, text="No recent generations yet.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=theme["TEXT_SECONDARY"]
            ).pack(pady=10)
            return

        for file_path in recent_files:
            filename = os.path.basename(file_path)

            item_frame = ctk.CTkFrame(self.history_list, fg_color=theme["CARD"], corner_radius=6, border_color=theme["BORDER"], border_width=1)
            item_frame.pack(fill="x", pady=3, padx=2)

            lbl = ctk.CTkLabel(item_frame, text=filename, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=theme["TEXT_PRIMARY"])
            lbl.pack(side="left", padx=10, pady=6)

            play_btn = ctk.CTkButton(
                item_frame, text="▶ Play", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                width=50, height=24, fg_color=theme["ACCENT_CYAN"], text_color="#000000",
                command=lambda f=file_path: self.app.load_and_play_history(f)
            )
            play_btn.pack(side="right", padx=8, pady=6)

    def update_speed_label(self, val):
        self.speed_value_label.configure(text=f"{int(round(float(val)))}/10")

    def update_volume_label(self, val):
        self.volume_value_label.configure(text=f"{int(round(float(val)))}%")

    def browse_file(self):
        initial_dir = self.app.settings.get("import_dir", os.path.expanduser("~"))
        path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Text & Document files", "*.txt *.docx *.pdf *.rtf *.odt")])
        if path:
            try:
                from backend import extract_text_from_file
                text = extract_text_from_file(path)
                self.text_entry.delete("1.0", ctk.END)
                self.text_entry.insert(ctk.END, text.strip())
            except Exception as e:
                messagebox.showerror("File Error", str(e))

    def update_voice_metadata(self, selected_voice_string):
        try:
            voice_index = int(selected_voice_string.split(":")[0])
            voice = self.app.voices[voice_index]
            gender_txt = voice.get("Gender", "Unknown")
            lang_txt = voice.get("Locale", "Unknown").split("-")[0]
            self.tag_gender.configure(text=f"Gender: {gender_txt.capitalize()}")
            self.tag_lang.configure(text=f"Lang: {lang_txt.upper()}")
        except Exception:
            self.tag_gender.configure(text="Gender: N/A")
            self.tag_lang.configure(text="Lang: N/A")

    def refresh(self):
        self.build_ui()