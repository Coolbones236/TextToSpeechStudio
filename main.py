import asyncio
import tkinter as tk
import customtkinter as ctk
from gui import TTSApp


async def run_tk_async(app: TTSApp, interval: float = 0.03):
    """Pumps the Tkinter event loop natively inside the asyncio loop."""
    try:
        while True:
            app.update()
            await asyncio.sleep(interval)
    except (tk.TclError, ctk.CTkError):
        pass


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = TTSApp(loop=loop)

    tk_task = loop.create_task(run_tk_async(app))

    try:
        loop.run_forever()
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        if pending:
            loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )

        loop.close()


if __name__ == "__main__":
    main()