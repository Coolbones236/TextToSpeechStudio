import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

FONT_FAMILY = "Segoe UI"


class SettingsView(ctk.CTkFrame):
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

        scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_container.grid(row=0, column=0, sticky="nsew", padx=30, pady=25)
        scroll_container.grid_columnconfigure(0, weight=1)

        # Card 1: Color Themes
        theme_card = ctk.CTkFrame(scroll_container, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        theme_card.pack(fill="x", pady=(0, 18))
        theme_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(theme_card, text="COLOR THEME & APPEARANCE", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=theme["ACCENT_PURPLE"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        ctk.CTkLabel(theme_card, text="Color Palette:", font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=theme["TEXT_PRIMARY"]).grid(row=1, column=0, sticky="w", padx=20, pady=10)

        self.theme_combo = ctk.CTkOptionMenu(
            theme_card, values=["Cyberpunk", "Ocean Breeze", "Forest", "Midnight"],
            fg_color=theme["CARD"], button_color=theme["CARD"], button_hover_color=theme["BORDER"],
            text_color=theme["TEXT_PRIMARY"], font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self.change_color_theme_action
        )
        self.theme_combo.set(self.app.settings.get("color_theme", "Cyberpunk"))
        self.theme_combo.grid(row=1, column=1, sticky="e", padx=20, pady=10)

        # Card 2: Directories
        paths_card = ctk.CTkFrame(scroll_container, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        paths_card.pack(fill="x", pady=(0, 18))
        paths_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(paths_card, text="STORAGE & DIRECTORY PATHS", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=theme["ACCENT_PURPLE"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        # Import Path
        ctk.CTkLabel(paths_card, text="Default Import Folder:", font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=theme["TEXT_PRIMARY"]).grid(row=1, column=0, sticky="w", padx=20, pady=10)

        self.import_path_lbl = ctk.CTkLabel(paths_card, text=self.app.settings.get("import_dir"), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=theme["TEXT_SECONDARY"])
        self.import_path_lbl.grid(row=1, column=1, sticky="w", padx=(10, 120), pady=10)

        change_imp_btn = ctk.CTkButton(
            paths_card, text="📁 Browse", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=theme["CARD"], border_color=theme["BORDER"], border_width=1, hover_color=theme["BORDER"],
            text_color=theme["TEXT_PRIMARY"], width=90, command=self.change_import_dir_action,
        )
        change_imp_btn.place(relx=1.0, rely=0.28, anchor="e", x=-20)

        # Export Path
        ctk.CTkLabel(paths_card, text="Default Export Folder:", font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=theme["TEXT_PRIMARY"]).grid(row=2, column=0, sticky="w", padx=20, pady=10)

        self.export_path_lbl = ctk.CTkLabel(paths_card, text=self.app.settings.get("export_dir"), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=theme["TEXT_SECONDARY"])
        self.export_path_lbl.grid(row=2, column=1, sticky="w", padx=(10, 120), pady=10)

        change_exp_btn = ctk.CTkButton(
            paths_card, text="📁 Browse", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=theme["CARD"], border_color=theme["BORDER"], border_width=1, hover_color=theme["BORDER"],
            text_color=theme["TEXT_PRIMARY"], width=90, command=self.change_export_dir_action,
        )
        change_exp_btn.place(relx=1.0, rely=0.55, anchor="e", x=-20)

        # Purge Cache
        purge_btn = ctk.CTkButton(
            paths_card, text="🧹 Purge Audio Preview Cache", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=theme["CARD"], border_color=theme["BORDER"], border_width=1, hover_color="#3D2020",
            text_color="#FF6B6B", command=self.clear_cache_action,
        )
        purge_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 15))

        # Card 3: Audio Defaults
        audio_card = ctk.CTkFrame(scroll_container, fg_color=theme["PANEL"], corner_radius=12, border_color=theme["BORDER"], border_width=1)
        audio_card.pack(fill="x", pady=(0, 18))
        audio_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(audio_card, text="EXPORT DEFAULTS", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=theme["ACCENT_PURPLE"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        ctk.CTkLabel(audio_card, text="Default Format:", font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=theme["TEXT_PRIMARY"]).grid(row=1, column=0, sticky="w", padx=20, pady=10)

        self.opt_default_format = ctk.CTkSegmentedButton(
            audio_card, values=[".mp3", ".wav"], selected_color=theme["ACCENT_CYAN"],
            selected_hover_color="#33D1B5", text_color=("#FFFFFF", "#000000"), command=self.on_format_updated,
        )
        current_fmt = self.app.settings.get("format", "mp3")
        self.opt_default_format.set(f".{current_fmt}" if not current_fmt.startswith(".") else current_fmt)
        self.opt_default_format.grid(row=1, column=1, sticky="e", padx=20, pady=10)

        save_btn = ctk.CTkButton(
            scroll_container, text="💾 Save Application Settings & Memory", font=ctk.CTkFont(family=FONT_FAMILY, weight="bold", size=13),
            fg_color=theme["ACCENT_CYAN"], hover_color="#33D1B5", text_color="#000000", height=42, command=self.save_settings_action,
        )
        save_btn.pack(fill="x", pady=(10, 20))

    def change_color_theme_action(self, selected_theme):
        self.app.settings["color_theme"] = selected_theme
        self.app.apply_theme_refresh()

    def on_format_updated(self, value):
        studio = self.app.frames.get("Studio")
        if studio and hasattr(studio, 'format_var'):
            studio.format_var.set(value)

    def change_import_dir_action(self):
        new_dir = filedialog.askdirectory(title="Select Default Import Directory")
        if new_dir:
            self.app.settings["import_dir"] = new_dir
            self.import_path_lbl.configure(text=new_dir)

    def change_export_dir_action(self):
        new_dir = filedialog.askdirectory(title="Select Default Export Directory")
        if new_dir:
            self.app.settings["export_dir"] = new_dir
            self.export_path_lbl.configure(text=new_dir)

    def save_settings_action(self):
        self.app.save_settings()
        messagebox.showinfo("Settings Saved", "Application memory and preferences saved successfully.")

    def clear_cache_action(self):
        if self.app.backend.is_playing():
            self.app.stop_audio()
        try:
            count = 0
            if os.path.exists(self.app.cache_dir):
                for file in os.listdir(self.app.cache_dir):
                    file_path = os.path.join(self.app.cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
            messagebox.showinfo("Cache Purged", f"Purged {count} temporary audio preview files.")
        except Exception as e:
            messagebox.showerror("Cache Clear Error", f"Failed to clear cache:\n{str(e)}")

    def refresh(self):
        self.build_ui()