
# main.py
import traceback
import threading
from vision_thread import main as vision_main
from game_loop import run_game



run_game()  # blocks until window closes
threading.Thread(target=vision_main, daemon=True)


if __name__ == "__main__":
    try:
        run_game()
    except Exception:
        print("🔥 CRASH:")
        traceback.print_exc()
        input("Press Enter to exit...")