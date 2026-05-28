# main.py
import threading
#from vision_thread import run_vision
from game_loop import run_game

#vision = threading.Thread(target=run_vision, daemon=True)
#vision.start()
run_game()  # blocks until window closes