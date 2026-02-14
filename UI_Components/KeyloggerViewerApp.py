import dearpygui.dearpygui as dpg
from LogFileManager import LogFileManager
from KeyloggerEngine import KeyloggerEngine
from PlatformUtils import PlatformUtils
from UI_Components.FileTreeWidget import FileTreeWidget
import datetime
from UI_Components.LogViewerWidget import LogViewerWidget
import os
import time
import glob
import queue
import threading


class KeyloggerViewerApp:
    """Main application - Dear PyGui version"""

    # Constants - These define magic numbers once at the top
    UPDATE_INTERVAL_SECONDS = 2.0
    KB_TO_MB_THRESHOLD = 1024  # Switch to MB after 1024 KB

    def __init__(self):
        # Initialize backend components
        self.get_active_window = PlatformUtils.setup_platform_libraries()
        self.file_manager = LogFileManager()

        # Thread-safe queue for UI updates
        self.log_update_queue = queue.Queue()

        self.keylogger = KeyloggerEngine(
            self.file_manager,
            self.get_active_window,
            log_update_queue=self.log_update_queue
        )

        self.current_viewing_file = None
        self.auto_scroll_enabled = True
        self.showing_calendar = True # Track which view is visible

        # State variables
        self.current_executable = "Not running"
        self.search_text = ""
        self.last_update_time = time.time()

        # Store UI element IDs
        self.ui_ids = {}

        # Build the UI
        self._create_button_themes()
        self.build_ui()

    def show_about(self):
        """Show about dialog"""
        with dpg.window(
                label="About",
                modal=True,
                show=True,
                tag="about_window",
                width=400,
                height=200,
                pos=(400, 250)
        ):
            dpg.add_text("Keylogger with Viewer", color=(100, 150, 255))
            dpg.add_text("Version 2.1 - Storage Monitor Edition")
            dpg.add_spacer(height=10)
            dpg.add_text("A modern keylogging and log viewing application")
            dpg.add_spacer(height=10)
            dpg.add_text("Built with:")
            dpg.add_text("  • Dear PyGui - GPU-accelerated UI")
            dpg.add_text("  • pynput - Keystroke capture")
            dpg.add_text("  • Python 3.7+")
            dpg.add_spacer(height=10)
            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item("about_window"),
                width=-1
            )

    def build_ui(self):
        """Build the entire UI"""
        with dpg.window(label="Keylogger with Viewer", tag="primary_window"):
            with dpg.handler_registry():
                dpg.add_key_press_handler(dpg.mvKey_F5, callback=lambda: self._refresh_viewer(None, None, None))

            with dpg.menu_bar():
                with dpg.menu(label="Help"):
                    dpg.add_menu_item(label="About", callback=lambda: self.show_about())

            with dpg.table(header_row=False, borders_innerV=True, tag="main_table"):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=320)
                dpg.add_table_column()

                with dpg.table_row():
                    with dpg.table_cell():
                        self._build_left_panel()
                    with dpg.table_cell():
                        self._build_right_panel()

    def _build_left_panel(self):
        """Build left panel: controls, tree, calendar"""
        self.ui_ids['start_btn'] = dpg.add_button(label="▶ Start Logging", callback=self._start_logging, width=-1)
        dpg.bind_item_theme(self.ui_ids['start_btn'], "green_button_theme")
        with dpg.tooltip(self.ui_ids['start_btn']):
            dpg.add_text("Begin recording all keystrokes")

        self.ui_ids['stop_btn'] = dpg.add_button(label="⏸ Stop Logging", callback=self._stop_logging, width=-1,
                                                 enabled=False)
        dpg.bind_item_theme(self.ui_ids['stop_btn'], "red_button_theme")
        with dpg.tooltip(self.ui_ids['stop_btn']):
            dpg.add_text("Stop recording keystrokes")

        dpg.add_spacer(height=5)
        # Removed redundant logging_status text

        # Restored Log Files header with click handler
        self.ui_ids['log_files_header'] = dpg.add_text("Log Files ▼", color=(200, 200, 255))
        
        # Make it clickable
        with dpg.item_handler_registry() as registry:
            dpg.add_item_clicked_handler(callback=self._toggle_calendar_view)
        dpg.bind_item_handler_registry(self.ui_ids['log_files_header'], registry)
        
        dpg.add_separator()

        # Removed search input
        with dpg.group(tag="calendar_group", show=True):
            dpg.add_text("Selected Date", color=(200, 200, 255))
            dpg.add_separator()

            default_date = {'month_day': datetime.datetime.now().day, 'year': datetime.datetime.now().year - 1900,
                            'month': datetime.datetime.now().month - 1}
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_spacer()
                    self.ui_ids['date_picker'] = dpg.add_date_picker(default_value=default_date)
                    dpg.add_spacer()

            dpg.add_spacer(height=10)
            dpg.add_button(label="Load Selected Date", callback=self._load_from_date_picker, width=-1)
            dpg.add_spacer(height=10)
            dpg.add_button(label="🔄 Refresh Current", callback=self._refresh_viewer, width=-1)
            dpg.add_spacer(height=20)


        # Use tag="file_tree_group" to match the toggle logic
        dpg.add_group(tag="file_tree_group", show=False) 
        self.file_tree = FileTreeWidget("file_tree_group", self.file_manager)
        self.file_tree.on_file_selected = self._on_file_selected
        self.file_tree.on_file_deleted = self._on_file_deleted
        self.file_tree.populate()
        dpg.add_separator()

    def _toggle_calendar_view(self, sender, app_data):
        """toggle between calendar and file tree views"""
        self.showing_calendar = not self.showing_calendar

        if self.showing_calendar:
            # show calendar, hide file tree
            dpg.configure_item("calendar_group", show=True)
            dpg.configure_item("file_tree_group", show=False)
            dpg.set_value(self.ui_ids['log_files_header'], "Log Files ▼")
        else:
            # show file tree, hide calendar
            dpg.configure_item("calendar_group", show=False)
            dpg.configure_item("file_tree_group", show=True)
            dpg.set_value(self.ui_ids['log_files_header'], "Log Files ▲")

    def _build_right_panel(self):
        """Build right panel: status, log viewer"""
        self._build_status_header()
        dpg.add_separator()
        dpg.add_spacer(height=5)

        with dpg.group(tag="log_viewer_container"):
            pass
        self.log_viewer = LogViewerWidget("log_viewer_container")

        dpg.add_checkbox(label="Auto-scroll", default_value=True, callback=self._on_autoscroll_toggled)

        with dpg.group(horizontal=True):
            dpg.add_text("Ready", tag="status_bar_text", color=(150, 150, 150))
            dpg.add_spacer(width=20)
            file_count = len(glob.glob("keylogs/keylog_*.txt"))
            dpg.add_text(f"Files: {file_count}", tag="file_count_text")

    def _start_logging(self, sender, app_data, user_data):
        """Start the keylogger"""
        dpg.configure_item(self.ui_ids['start_btn'], enabled=False)
        dpg.configure_item(self.ui_ids['stop_btn'], enabled=True)
        # Removed logging_status update
        dpg.set_value(self.ui_ids['status_label'], "Logging")
        dpg.configure_item(self.ui_ids['status_label'], color=(0, 255, 0))

        threading.Thread(target=self.keylogger.start, daemon=True).start()

        today_log_file = self.file_manager.get_log_filename()
        self.current_viewing_file = today_log_file
        if not os.path.exists(today_log_file):
            with open(today_log_file, 'w', encoding='utf-8') as f:
                f.write("")

        # Use load_file instead of _refresh_log_viewer to set current_filepath
        self.log_viewer.load_file(today_log_file, self.file_manager)
        self.log_viewer.set_auto_scroll(True)

        # Update storage indicator immediately
        self._update_storage_indicator()

    def _stop_logging(self, sender, app_data, user_data):
        """Stop the keylogger"""
        self.keylogger.stop()
        dpg.configure_item(self.ui_ids['start_btn'], enabled=True)
        dpg.configure_item(self.ui_ids['stop_btn'], enabled=False)
        # Removed logging_status update
        dpg.set_value(self.ui_ids['status_label'], "Stopped")
        dpg.configure_item(self.ui_ids['status_label'], color=(255, 0, 0))

    def _load_from_date_picker(self, sender, app_data, user_data):
        """Load log file from date picker selection"""
        date_data = dpg.get_value(self.ui_ids['date_picker'])
        selected_date = datetime.datetime(year=date_data['year'] + 1900, month=date_data['month'] + 1,
                                          day=date_data['month_day'])
        filepath = self.file_manager.get_log_filename(selected_date)

        if os.path.exists(filepath):
            self.log_viewer.load_file(filepath, self.file_manager)
            # Update storage indicator immediately
            self._update_storage_indicator()
        else:
            self.log_viewer.update_content(f"No logfile found for {selected_date.strftime('%B %d, %Y')}")
            # No file, so storage should show 0 KB
            self._update_storage_indicator()

    def _refresh_log_viewer(self, filepath, auto_scroll=False):
        """Reload log content and optionally scroll to bottom"""
        try:
            content = self.file_manager.read_file(filepath)
            self.log_viewer.update_content(content)
            if auto_scroll and self.auto_scroll_enabled:
                self.log_viewer.set_auto_scroll(True)
        except Exception as e:
            print(f"Error refreshing log viewer: {e}")

    def _refresh_viewer(self, sender, app_data, user_data):
        """Refresh the current viewer (Manual refresh)"""
        if self.keylogger.is_running:
            today = datetime.datetime.now()
            self._refresh_log_viewer(
                self.file_manager.get_log_filename(today),
                auto_scroll=True
            )
        elif self.current_viewing_file:
            self._refresh_log_viewer(self.current_viewing_file)

    #def _on_search_changed(self, sender, app_data, user_data):
     #   self.file_tree.populate(dpg.get_value(sender))

    def _on_file_selected(self, filepath):
        self.current_viewing_file = filepath
        self.log_viewer.load_file(filepath, self.file_manager)
        # Immediately update storage indicator for the selected file
        self._update_storage_indicator()

    def _on_file_deleted(self, filepath):
        if self.log_viewer.current_filepath == filepath:
            self.log_viewer.clear()
            # Update storage to show 0 KB
            self._update_storage_indicator()

    def _on_autoscroll_toggled(self, sender, app_data, user_data):
        self.auto_scroll_enabled = app_data
        self.log_viewer.set_auto_scroll(self.auto_scroll_enabled)

    def _build_status_header(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Status:", color=(200, 200, 200))
            self.ui_ids['status_label'] = dpg.add_text("Ready", color=(255, 165, 0))
            dpg.add_spacer(width=20)
            dpg.add_text("|", color=(100, 100, 100))
            dpg.add_spacer(width=20)
            dpg.add_text("Tracking:", color=(200, 200, 200))
            self.ui_ids['executable_label'] = dpg.add_text("Not running", color=(100, 150, 255))

    def _update_loop(self):
        """Called every frame - checks for updates from background threads."""
        try:
            while not self.log_update_queue.empty():
                log_file = self.log_update_queue.get_nowait()
                if self.current_viewing_file == log_file:
                    self._refresh_log_viewer(log_file, auto_scroll=True)
        except queue.Empty:
            pass

        current_time = time.time()
        if current_time - self.last_update_time >= self.UPDATE_INTERVAL_SECONDS:
            self.last_update_time = current_time
            self._update_status()

    def _update_status(self):
        """Update status labels and refresh data."""
        if self.keylogger.is_running:
            try:
                self.current_executable = self.get_active_window()
                dpg.set_value(self.ui_ids['executable_label'], self.current_executable)
            except:
                dpg.set_value(self.ui_ids['executable_label'], "Unknown")

        else:
            dpg.set_value(self.ui_ids['executable_label'], "Not running")

        file_count = len(glob.glob("keylogs/keylog_*.txt"))
        dpg.set_value("file_count_text", f"Files: {file_count}")

        # NEW: Update storage indicator
        self._update_storage_indicator()

    # ==================================================================
    # NEW METHODS: Storage Monitoring Feature
    # ==================================================================

    def _get_current_file_size(self):
        """
        Calculate the size of the currently viewed log file in bytes.

        Returns:
            int: File size in bytes, or 0 if no file is selected

        Principle: Single Responsibility - This method does ONE thing
        """
        # Get the filepath of the currently viewed file
        current_file = self.log_viewer.current_filepath

        if not current_file:
            return 0  # No file selected

        try:
            if os.path.exists(current_file):
                size = os.path.getsize(current_file)
                return size
            else:
                return 0
        except OSError as e:
            # Defensive programming - handle potential errors
            print(f"Error getting file size: {e}")
            return 0

    def _format_file_size(self, size_bytes):
        """
        Format file size with appropriate unit (KB or MB).

        Args:
            size_bytes (int): Size in bytes

        Returns:
            str: Formatted string like "125 KB" or "1.5 MB"

        Principle: Separation of Concerns - Logic is separate from display
        """
        size_kb = size_bytes / 1024.0

        if size_kb < self.KB_TO_MB_THRESHOLD:
            # Display in KB
            return f"{size_kb:.1f} KB"
        else:
            # Convert to MB when exceeding threshold
            size_mb = size_kb / 1024.0
            return f"{size_mb:.2f} MB"

    def _get_storage_color(self, size_bytes):
        """
        Determine color based on file size.

        Args:
            size_bytes (int): Size in bytes

        Returns:
            tuple: RGB color tuple

        Principle: DRY (Don't Repeat Yourself) - Centralize color logic
        """
        size_kb = size_bytes / 1024.0

        if size_kb < 100:
            return (150, 200, 255)  # Light blue - normal
        elif size_kb < 512:
            return (255, 200, 100)  # Orange - warning
        else:
            return (255, 100, 100)  # Red - high usage

    def _update_storage_indicator(self):
        """
        Update the storage indicator in the log viewer.

        Shows the size of the currently selected/viewed file.

        Principle: Composition - Combines smaller methods to achieve goal
        """
        size_bytes = self._get_current_file_size()
        formatted_size = self._format_file_size(size_bytes)
        color = self._get_storage_color(size_bytes)

        # Update the storage display in the log viewer widget
        self.log_viewer.update_storage(formatted_size, color)

    def _create_button_themes(self):
        with dpg.theme(tag="green_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (16, 124, 16))
        with dpg.theme(tag="red_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 16, 16))