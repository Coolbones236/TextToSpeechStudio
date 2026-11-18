import asyncio
import os
import shutil
import tempfile
import docx
import PyPDF2
import pypandoc
import pygame
import edge_tts


def extract_text_from_file(path: str) -> str:
    """Parses text safely from various document formats."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".docx":
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    elif ext == ".pdf":
        text_chunks = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_chunks.append(extracted)
        return "\n".join(text_chunks)
    elif ext in [".rtf", ".odt"]:
        return pypandoc.convert_file(path, "plain")
    else:
        raise ValueError(f"Unsupported file format: {ext}")


class TTSProcessor:
    """Handles text-to-speech engine, audio generation, and playback using edge-tts and pygame."""

    def __init__(self, cache_dir: str):
        self.voices = []
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    async def load_voices_async(self) -> list[dict]:
        """Asynchronously fetches available voices from edge-tts."""
        all_voices = await edge_tts.list_voices()
        self.voices = [v for v in all_voices if v.get("Locale") == "en-US"]
        return self.voices

    def get_voices(self) -> list[dict]:
        return self.voices

    async def generate_audio_async(
        self,
        text: str,
        voice_id: str,
        speed_level: int,
        volume_level: float,
        fmt: str,
        save_path: str
    ):
        """Asynchronously generates audio without blocking the event loop or GUI thread."""
        speed_level = max(1, min(10, speed_level))
        volume_level = max(0.0, min(1.0, volume_level))

        rate_percent = int((speed_level - 5) * 20)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        vol_percent = int((volume_level - 1.0) * 100)
        vol_str = f"+{vol_percent}%" if vol_percent >= 0 else f"{vol_percent}%"

        communicate = edge_tts.Communicate(text, voice_id, rate=rate_str, volume=vol_str)

        temp_fd, temp_mp3 = tempfile.mkstemp(suffix=".mp3", dir=self.cache_dir)
        os.close(temp_fd)

        try:
            await communicate.save(temp_mp3)

            if fmt.lower() == "wav":
                try:
                    from pydub import AudioSegment
                except ImportError as exc:
                    raise RuntimeError("WAV export requires pydub and FFmpeg installed.") from exc

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    self._convert_mp3_to_wav,
                    temp_mp3,
                    save_path
                )
            else:
                if os.path.exists(save_path):
                    self.stop()
                    os.remove(save_path)
                os.replace(temp_mp3, save_path)
        finally:
            if os.path.exists(temp_mp3):
                try:
                    os.remove(temp_mp3)
                except OSError:
                    pass

    @staticmethod
    def _convert_mp3_to_wav(mp3_path: str, wav_path: str):
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")

    def play(self, file_path: str) -> float:
        self.stop()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        sound = pygame.mixer.Sound(file_path)
        length = sound.get_length()
        del sound
        return length

    def pause(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.pause()

    def resume(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.unpause()

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

    def is_playing(self) -> bool:
        if not pygame.mixer.get_init():
            return False
        return bool(pygame.mixer.music.get_busy())

    def cleanup_cache(self):
        """Purges sound preview cache directory and shuts down Pygame audio engine."""
        self.stop()
        if pygame.mixer.get_init():
            pygame.mixer.quit()

        if os.path.exists(self.cache_dir):
            try:
                shutil.rmtree(self.cache_dir)
            except Exception as e:
                print(f"Error purging sound cache: {e}")