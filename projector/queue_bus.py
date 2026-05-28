import queue

# One shared instance imported by both vision_thread and game_loop.
# maxsize=32 means if the game loop lags and can't drain fast enough,
# old events get dropped rather than RAM growing unbounded.
event_queue: queue.Queue = queue.Queue(maxsize=32)