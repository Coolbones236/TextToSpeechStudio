import asyncio
import json
import os
import queue
import shutil
import time

import customtkinter as ctk
from tkinter import filedialog, messagebox

from backend import TTSProcessor
from views import StudioView, HistoryView, SettingsView

FONT_FAMILY = "Segoe UI"

COLOR_THEMES = {
    "Cyberpunk": {
        "BG": "#0F131F", "SIDEBAR": "#151A28", "PANEL": "#151A28", "CARD": "#1C2333",
        "ACCENT_PURPLE": "#C5A3FF", "ACCENT_CYAN": "#45F0D1", "TEXT_PRIMARY": "#FFFFFF",
        "TEXT_SECONDARY": "#94A3B8", "BORDER": "#2A344A", "BTN_HOVER": "#2A344A"
    },
    "Ocean Breeze": {
        "BG": "#0F172A", "SIDEBAR": "#1E293B", "PANEL": "#1E293B", "CARD": "#334155",
        "ACCENT_PURPLE": "#38BDF8", "ACCENT_CYAN": "#34D399", "TEXT_PRIMARY": "#F8FAFC",
        "TEXT_SECONDARY": "#94A3B8", "BORDER": "#475569", "BTN_HOVER": "#475569"
    },
    "Forest": {
        "BG": "#061A14", "SIDEBAR": "#0B2920", "PANEL": "#0B2920", "CARD": "#12382C",
        "ACCENT_PURPLE": "#34D399", "ACCENT_CYAN": "#A7F3D0", "TEXT_PRIMARY": "#ECFDF5",
        "TEXT_SECONDARY": "#6EE7B7", "BORDER": "#1F4E3D", "BTN_HOVER": "#1F4E3D"
    },
    "Midnight": {
        "BG": "#09090B", "SIDEBAR": "#18181B", "PANEL": "#18181B", "CARD": "#27272A",
        "ACCENT_PURPLE": "#A855F7", "ACCENT_CYAN": "#EC4899", "TEXT_PRIMARY": "#FAFAFA",
        "TEXT_SECONDARY": "#A1A1AA", "BORDER": "#3F3F46", "BTN_HOVER": "#3F3F46"
    }
}


class TTSApp(ctk.CTk):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()

        self.loop = loop
        self.title("Text To Speech Studio")
        self.geometry("1200x800")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.gui_queue = queue.Queue()
        self.bind("<<DispatchGUI>>", self._process_gui_queue)

        self.config_dir = os.path.join(os.path.expanduser("~"), "Documents", "TextToSpeechStudio")
        self.cache_dir = os.path.join(self.config_dir, "Cache")
        self.config_file = os.path.join(self.config_dir, "config.json")

        self.load_settings()

        self.backend = TTSProcessor(cache_dir=self.cache_dir)
        self.audio_file = ""
        self.temp_audio_path = ""
        self.is_paused = False
        self.duration = 0.0
        self.start_time = 0.0
        self.recent_generations = []
        self.voices = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar_btns = {}
        self.create_sidebar()
        self.create_top_bar()

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=1, rowspan=2, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {
            "Studio": StudioView(self.main_container, self),
            "History": HistoryView(self.main_container, self),
            "Settings": SettingsView(self.main_container, self),
        }

        self.apply_theme_refresh()
        self.navigate("Studio")
        self.loop.create_task(self._init_voices_async())

    def get_theme_colors(self):
        theme_name = self.settings.get("color_theme", "Cyberpunk")
        return COLOR_THEMES.get(theme_name, COLOR_THEMES["Cyberpunk"])

    def apply_theme_refresh(self):
        theme = self.get_theme_colors()
        self.configure(fg_color=theme["BG"])
        self.sidebar_frame.configure(fg_color=theme["SIDEBAR"])
        self.top_bar_frame.configure(fg_color=theme["BG"])
        self.title_lbl.configure(text_color=theme["ACCENT_PURPLE"])
        self.top_title_lbl.configure(text_color=theme["ACCENT_PURPLE"])

        for frame in self.frames.values():
            if hasattr(frame, "refresh"):
                frame.refresh()

        self.update_sidebar_button_styles(self.active_page if hasattr(self, 'active_page') else "Studio")

    def dispatch_gui_task(self, func, *args, **kwargs):
        self.gui_queue.put((func, args, kwargs))
        try:
            self.event_generate("<<DispatchGUI>>", when="tail")
        except Exception:
            pass

    def _process_gui_queue(self, event=None):
        while not self.gui_queue.empty():
            try:
                func, args, kwargs = self.gui_queue.get_nowait()
                func(*args, **kwargs)
                self.gui_queue.task_done()
            except queue.Empty:
                break

    def load_settings(self):
        self.settings = {
            "voice_index": 0, "speed": 5, "volume": 100,
            "format": "mp3", "color_theme": "Cyberpunk",
            "import_dir": os.path.expanduser("~"),
            "export_dir": os.path.join(self.config_dir, "Exports"),
            "recent_generations": []
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.settings.update(json.load(f))
            except Exception:
                pass

        self.recent_generations = self.settings.get("recent_generations", [])
        ctk.set_appearance_mode("Dark")

    def save_settings(self):
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            studio = self.frames.get("Studio")
            if studio and hasattr(studio, 'voice_var') and studio.voice_var.get() and ":" in studio.voice_var.get():
                prefix = studio.voice_var.get().split(":")[0]
                if prefix.isdigit():
                    self.settings["voice_index"] = int(prefix)
                self.settings["speed"] = studio.speed_slider.get()
                self.settings["volume"] = studio.volume_slider.get()
                self.settings["format"] = studio.format_var.get().replace(".", "")

            self.settings["recent_generations"] = self.recent_generations

            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def on_closing(self):
        self.withdraw()
        self.save_settings()
        self.backend.cleanup_cache()

        try:
            for after_id in self.tk.call('after', 'info'):
                self.after_cancel(after_id)
        except Exception:
            pass

        if self.loop.is_running():
            self.loop.stop()

        try:
            self.destroy()
        except Exception:
            pass

    def reload_voices(self):
        """Allows manually re-fetching system voices."""
        studio = self.frames.get("Studio")
        if studio:
            studio.voice_combo.configure(values=["Fetching voices..."])
            studio.voice_var.set("Fetching voices...")
            studio.tag_gender.configure(text="Gender: N/A")
            studio.tag_lang.configure(text="Lang: N/A")

        self.loop.create_task(self._init_voices_async())

    async def _init_voices_async(self):
        try:
            self.voices = await self.backend.load_voices_async()
            if not self.voices:
                raise RuntimeError("No voices were returned.")
            self.dispatch_gui_task(self._populate_voice_dropdown)
        except Exception as e:
            def on_fail():
                studio = self.frames.get("Studio")
                if studio:
                    studio.voice_combo.configure(values=["Error loading voices"])
                    studio.voice_var.set("Error loading voices")
                messagebox.showerror("Voice Load Error", f"Failed to fetch voices online:\n{e}\n\nClick the 🔄 Refresh button to try again.")
            self.dispatch_gui_task(on_fail)

    def _populate_voice_dropdown(self):
        voice_names = [f"{i}: {v.get('ShortName', 'Voice ' + str(i))}" for i, v in enumerate(self.voices)]
        saved_v_idx = self.settings.get("voice_index", 0)
        if saved_v_idx >= len(voice_names): saved_v_idx = 0

        studio = self.frames["Studio"]
        if voice_names:
            studio.voice_combo.configure(values=voice_names)
            selected = voice_names[saved_v_idx]
            studio.voice_var.set(selected)
            studio.update_voice_metadata(selected)

    def create_sidebar(self):
        theme = self.get_theme_colors()
        self.sidebar_frame = ctk.CTkFrame(self, fg_color=theme["SIDEBAR"], corner_radius=0, width=220)
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.title_lbl = ctk.CTkLabel(self.sidebar_frame, text="Text To Speech", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=theme["ACCENT_PURPLE"])
        self.title_lbl.grid(row=0, column=0, padx=20, pady=(30, 0), sticky="w")

        ctk.CTkLabel(self.sidebar_frame, text="Studio Edition", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=theme["TEXT_SECONDARY"]).grid(row=1, column=0, padx=20, pady=(0, 30), sticky="w")

        menu_items = {"Studio": "🎙️", "History": "🕒"}
        for i, (item, icon) in enumerate(menu_items.items()):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"  {icon}   {item}", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color="transparent", text_color=theme["TEXT_PRIMARY"], hover_color=theme["BTN_HOVER"],
                anchor="w", corner_radius=8, height=42, command=lambda name=item: self.navigate(name)
            )
            btn.grid(row=i + 2, column=0, padx=15, pady=5, sticky="ew")
            self.sidebar_btns[item] = (btn, icon)

        settings_btn = ctk.CTkButton(
            self.sidebar_frame, text="  ⚙️   Settings", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color="transparent", text_color=theme["TEXT_PRIMARY"], hover_color=theme["BTN_HOVER"],
            anchor="w", corner_radius=8, height=42, command=lambda name="Settings": self.navigate(name)
        )
        settings_btn.grid(row=8, column=0, padx=15, pady=(5, 20), sticky="ew")
        self.sidebar_btns["Settings"] = (settings_btn, "⚙️")

    def create_top_bar(self):
        theme = self.get_theme_colors()
        self.top_bar_frame = ctk.CTkFrame(self, fg_color=theme["BG"], corner_radius=0, height=70)
        self.top_bar_frame.grid(row=0, column=1, sticky="ew")
        self.top_title_lbl = ctk.CTkLabel(self.top_bar_frame, text="Studio Workspace", font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"), text_color=theme["ACCENT_PURPLE"])
        self.top_title_lbl.grid(row=0, column=0, padx=30, pady=20, sticky="w")

    def update_sidebar_button_styles(self, active_page):
        theme = self.get_theme_colors()
        for name, (btn, icon) in self.sidebar_btns.items():
            if name == active_page:
                btn.configure(
                    fg_color=theme["CARD"],
                    text_color=theme["ACCENT_CYAN"],
                    border_color=theme["ACCENT_CYAN"],
                    border_width=1,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                    text=f" ➡️ {icon}  {name}"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=theme["TEXT_PRIMARY"],
                    border_width=0,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    text=f"  {icon}   {name}"
                )

    def navigate(self, page_name):
        self.active_page = page_name
        self.top_title_lbl.configure(text=f"{page_name} Workspace" if page_name != "Settings" else "Application Settings")
        self.update_sidebar_button_styles(page_name)

        for name, frame in self.frames.items():
            if name == page_name:
                frame.grid(row=0, column=0, sticky="nsew")
                if hasattr(frame, "refresh"):
                    frame.refresh()
            else:
                frame.grid_forget()

    def get_all_exported_files(self):
        export_dir = self.settings.get("export_dir", os.path.join(self.config_dir, "Exports"))
        files = []
        if os.path.exists(export_dir):
            for file in os.listdir(export_dir):
                if file.lower().endswith((".mp3", ".wav")):
                    files.append(os.path.join(export_dir, file))
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files

    def generate_preview(self):
        studio = self.frames["Studio"]

        if not self.voices:
            messagebox.showwarning("Voices Loading", "System voices are still fetching. Please wait a moment or click Refresh.")
            return

        voice_str = studio.voice_var.get()
        if not voice_str or ":" not in voice_str or not voice_str.split(":")[0].isdigit():
            messagebox.showwarning("Voices Not Ready", "Voices are unavailable. Click the 🔄 Refresh button to reload.")
            return

        text = studio.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Missing Text", "Please enter text or import a document.")
            return

        if self.backend.is_playing(): self.stop_audio()
        fmt = studio.format_var.get().replace(".", "")
        self.temp_audio_path = os.path.join(self.cache_dir, f"preview_{os.urandom(4).hex()}.{fmt}")

        studio.status_label.configure(text="Status: Generating preview...")
        studio.gen_btn.configure(state="disabled")
        studio.download_btn.configure(state="disabled")

        self.loop.create_task(self._run_async_generation(text, fmt, self.temp_audio_path))

    async def _run_async_generation(self, text: str, fmt: str, save_path: str):
        studio = self.frames["Studio"]
        try:
            voice_str = studio.voice_var.get()
            voice_index = int(voice_str.split(":")[0])
            voice_id = self.voices[voice_index]["ShortName"]
            speed = int(round(studio.speed_slider.get()))
            volume = float(studio.volume_slider.get()) / 100.0

            await self.backend.generate_audio_async(text, voice_id, speed, volume, fmt, save_path)

            def success():
                self.audio_file = save_path
                studio.play_btn.configure(state="normal")
                studio.status_label.configure(text="Status: ✅ Preview ready")
                studio.gen_btn.configure(state="normal")
                studio.download_btn.configure(state="normal")

            self.dispatch_gui_task(success)
        except Exception as e:
            err = str(e)
            def failure():
                studio.gen_btn.configure(state="normal")
                studio.download_btn.configure(state="disabled")
                studio.status_label.configure(text="Status: Error")
                messagebox.showerror("Error", f"Generation failed:\n{err}")
            self.dispatch_gui_task(failure)

    def download_audio(self):
        if not self.audio_file or not os.path.exists(self.audio_file):
            messagebox.showwarning("No Audio", "Please generate a preview first.")
            return

        studio = self.frames["Studio"]
        fmt = studio.format_var.get().replace(".", "")
        export_dir = self.settings.get("export_dir", os.path.join(self.config_dir, "Exports"))
        os.makedirs(export_dir, exist_ok=True)

        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}", initialdir=export_dir,
            filetypes=[(f"{fmt.upper()} files", f"*.{fmt}")],
        )

        if save_path:
            try:
                shutil.copy2(self.audio_file, save_path)
                studio.status_label.configure(text="Status: ✅ Saved successfully")
                if save_path not in self.recent_generations:
                    self.recent_generations.insert(0, save_path)
                    self.save_settings()
                    studio.refresh_recent_generations()
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def play_audio(self):
        if not self.audio_file or not os.path.exists(self.audio_file):
            return
            
        self.is_paused = False
        self.pause_start_time = 0.0
        self.total_paused_duration = 0.0
        
        self.duration = self.backend.play(self.audio_file) or 1.0
        
        studio = self.frames["Studio"]
        studio.play_btn.configure(state="disabled")
        studio.pause_btn.configure(state="normal")
        studio.stop_btn.configure(state="normal")
        studio.status_label.configure(text="Status: ▶️ Playing...")
        
        self.start_time = time.time()
        self.update_progress()

    def pause_audio(self):
        if not self.is_paused:
            self.backend.pause()
            self.is_paused = True
            self.pause_start_time = time.time()
            
            studio = self.frames["Studio"]
            studio.play_btn.configure(state="normal")
            studio.pause_btn.configure(state="disabled")
            studio.status_label.configure(text="Status: ⏸ Paused")

    def resume_audio(self):
        if self.is_paused:
            # Accumulate the time spent in paused state
            if self.pause_start_time > 0:
                self.total_paused_duration += time.time() - self.pause_start_time
                self.pause_start_time = 0.0

            self.backend.resume()
            self.is_paused = False
            
            studio = self.frames["Studio"]
            studio.play_btn.configure(state="disabled")
            studio.pause_btn.configure(state="normal")
            studio.status_label.configure(text="Status: ▶️ Playing...")
            self.update_progress()

    def stop_audio(self):
        self.backend.stop()
        self.reset_controls()
        self.frames["Studio"].status_label.configure(text="Status: ⏹️ Stopped")

    def update_progress(self):
        studio = self.frames["Studio"]
        
        if self.is_paused:
            return  # Stop progress loop while paused

        if self.backend.is_playing():
            # Calculate actual active playback time subtracting paused duration
            elapsed = time.time() - self.start_time - self.total_paused_duration
            elapsed = max(0.0, elapsed)
            percent = min((elapsed / self.duration), 1.0)
            
            studio.progress_bar.set(percent)

            e_min, e_sec = divmod(int(elapsed), 60)
            d_min, d_sec = divmod(int(self.duration), 60)
            studio.time_label.configure(text=f"{e_min:02d}:{e_sec:02d} / {d_min:02d}:{d_sec:02d} ({int(percent*100)}%)")

            self.after(100, self.update_progress)
        else:
            studio.status_label.configure(text="Status: ✅ Finished")
            self.reset_controls()

    def reset_controls(self):
        studio = self.frames["Studio"]
        self.is_paused = False
        self.pause_start_time = 0.0
        self.total_paused_duration = 0.0
        
        studio.play_btn.configure(state="normal" if self.audio_file else "disabled")
        studio.pause_btn.configure(state="disabled")
        studio.stop_btn.configure(state="disabled")
        studio.progress_bar.set(0)
        studio.time_label.configure(text="00:00 / 00:00 (0%)")

    def load_and_play_history(self, file_path):
        if os.path.exists(file_path):
            if self.backend.is_playing(): self.stop_audio()
            self.audio_file = file_path
            studio = self.frames["Studio"]
            studio.download_btn.configure(state="normal")
            self.play_audio()
        else:
            messagebox.showerror("File Not Found", f"Could not locate file:\n{file_path}")