

import dearpygui.dearpygui as dpg
from LogFileManager import LogFileManager
from KeyloggerEngine import KeyloggerEngine
from PlatformUtils import PlatformUtils
from UI_Components import FileTreeWidget
from UI_Components.FileTreeWidget import FileTreeWidget
import datetime
from UI_Components.LogViewerWidget import LogViewerWidget
import os
import time
import glob


class KeyloggerViewerApp:
    """Main application - Dear PyGui version"""
    def __init__(self):
        # Initialize backend components (no changes from tkinter version)
        self.get_active_window = PlatformUtils.setup_platform_libraries()
        self.file_manager = LogFileManager()
        self.keylogger = KeyloggerEngine(self.file_manager, self.get_active_window)

        # State variables
        self.current_executable = "Not running"
        self.search_text = ""

        # Store UI element IDs (NEW  we need these for updates)
        self.ui_ids = {}

        self._create_button_themes()

        # Build the UI
        self.build_ui()
        self.last_update_time = time.time()

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
            dpg.add_text("Version 2.0 - Dear PyGui Edition")
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

        # Create main window
        with dpg.window(label="Keylogger with Viewer", tag="primary_window"):

            # The menu bar and handlers must be created INSIDE the window they belong to.
            with dpg.handler_registry():
                dpg.add_key_press_handler(dpg.mvKey_F5, callback=lambda: self._refresh_viewer(None, None, None))
                # The Delete key handler is more complex and requires getting the selected tree item.
                # This is a placeholder for future implementation.
                # dpg.add_key_press_handler(dpg.mvKey_Delete, callback=self._handle_delete_key)

            with dpg.menu_bar():
                with dpg.menu(label="Help"):
                    dpg.add_menu_item(label="About", callback=lambda: self.show_about())

            # Create 2-column table layout
            with dpg.table(header_row=False, borders_innerV=True, tag="main_table"):

                # Column 0: Left panel (fixed width)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=320)

                # Column 1: Right panel (fills remaining space)
                dpg.add_table_column()

                # Single row containing both columns
                with dpg.table_row():

                    # LEFT PANEL (Column 0)
                    with dpg.table_cell():
                            self._build_left_panel()

                    # RIGHT PANEL (Column 1)
                    with dpg.table_cell():
                        self._build_right_panel()





    def _build_left_panel(self):
        """Build left panel: controls, tree, calendar"""

        # --- Control Panel ---
        self.ui_ids['start_btn'] = dpg.add_button(
            label="▶ Start Logging",
            callback=self._start_logging,
            width=-1
        )
        dpg.bind_item_theme(self.ui_ids['start_btn'], "green_button_theme")

        with dpg.tooltip(self.ui_ids['start_btn']):
            dpg.add_text("Begin recording all keystrokes")
            dpg.add_text("Logs will be saved to keylogs/", color=(150, 150, 150))

        self.ui_ids['stop_btn'] = dpg.add_button(
            label="⏸ Stop Logging",
            callback=self._stop_logging,
            width=-1,
            enabled=False
        )
        dpg.bind_item_theme(self.ui_ids['stop_btn'], "red_button_theme")

        # === ADD THIS: Tooltip for Stop button ===
        with dpg.tooltip(self.ui_ids['stop_btn']):
            dpg.add_text("Stop recording keystrokes")
            dpg.add_text("Current log file will be saved", color=(150, 150, 150))

        dpg.add_spacer(height=5)
        self.ui_ids['logging_status'] = dpg.add_text(
            "● Stopped",
            color=(255, 0, 0)
        )

        dpg.add_text("Log Files", color=(200, 200, 255))
        dpg.add_separator()

        # Search box
        self.ui_ids['search_input'] = dpg.add_input_text(
            label="🔍 Search",
            callback=self._on_search_changed,
            width=-1
        )
        dpg.add_spacer(height=10)

        dpg.add_spacer(height=20)
        dpg.add_text("Selected Date", color=(200, 200, 255))
        dpg.add_separator()

        # Date picker
        default_date = {
            'month_day': datetime.datetime.now().day,
            'year': datetime.datetime.now().year - 1900, # Fix: DPG uses years since 1900
            'month': datetime.datetime.now().month - 1 # 0-indexed
        }

        self.ui_ids['date_picker'] = dpg.add_date_picker(
            default_value=default_date,
            callback=self._on_date_selected
        )

        dpg.add_spacer(height=10)

        # Load button
        load_date_btn = dpg.add_button(
            label="Load Selected Date",
            callback=self._load_from_date_picker,
            width=-1
        )

        with dpg.tooltip(load_date_btn):
            dpg.add_text("Load log file for the selected date")
            dpg.add_text("Shows keystrokes recorded on that day", color=(150, 150, 150))

        dpg.add_spacer(height=10)

        # Refresh button
        refresh_btn = dpg.add_button(
            label="🔄 Refresh Current",
            callback=self._refresh_viewer,
            width=-1
        )

        # === ADD THIS: Tooltip for Refresh button ===
        with dpg.tooltip(refresh_btn):
            dpg.add_text("Reload the currently displayed log file")
            dpg.add_text("Hotkey: F5", color=(150, 150, 150))

        dpg.add_spacer(height=20)
        dpg.add_separator()


        # Add container for tree (Must be created BEFORE the widget)
        dpg.add_group(tag="file_tree_container")

        # Create tree widget
        self.file_tree = FileTreeWidget("file_tree_container", self.file_manager)
        self.file_tree.on_file_selected = self._on_file_selected
        self.file_tree.on_file_deleted = self._on_file_deleted

        self.file_tree.populate() # Initial population

        dpg.add_separator()

    def _start_logging(self, sender, app_data, user_data):
        """Start the keylogger"""
        # Disable start button
        dpg.configure_item(self.ui_ids['start_btn'], enabled=False)

        # Enable stop button
        dpg.configure_item(self.ui_ids['stop_btn'], enabled=True)

        # Update status
        dpg.set_value(self.ui_ids['logging_status'], "● Logging")
        dpg.configure_item(self.ui_ids['logging_status'], color=(0, 255, 0))  # Green

        # FIX: Update the main status label in the header
        dpg.set_value(self.ui_ids['status_label'], "Logging")
        dpg.configure_item(self.ui_ids['status_label'], color=(0, 255, 0))

        # Start keylogger engine (same as before)
        import threading
        threading.Thread(target=self.keylogger.start, daemon=True).start()

        print("Keylogger started")

    def _stop_logging(self, sender, app_data, user_data):
        """Stop the keylogger"""
        # Stop keylogger engine
        self.keylogger.stop()

        # Enable start button
        dpg.configure_item(self.ui_ids['start_btn'], enabled=True)

        # Disable stop button
        dpg.configure_item(self.ui_ids['stop_btn'], enabled=False)

        # Update status
        dpg.set_value(self.ui_ids['logging_status'], "● Stopped")
        dpg.configure_item(self.ui_ids['logging_status'], color=(255, 0, 0))  # Red

        # FIX: Update the main status label in the header
        dpg.set_value(self.ui_ids['status_label'], "Stopped")
        dpg.configure_item(self.ui_ids['status_label'], color=(255, 0, 0))

        print("Keylogger stopped")



    def _on_date_selected(self, sender, app_data, user_data):
        """Handle date picker selection"""
        # app_data contains: {'month_day': day, 'year': year,, 'month': month}
        print(f"Date selected: {app_data}")



    def _load_from_date_picker(self, sender, app_data, user_data):
        """Load log file from date picker selection"""
        # Get selected date
        date_data = dpg.get_value(self.ui_ids['date_picker'])


        # Convert to datetime
        selected_date = datetime.datetime(
            year=date_data['year'] + 1900,
            month=date_data['month'] + 1,
            day=date_data['month_day']
        )

        # Get filepath
        filepath = self.file_manager.get_log_filename(selected_date)

        # Load if exists
        if os.path.exists(filepath):
            self.log_viewer.load_file(filepath, self.file_manager)
        else:
            # Show "not found" message
            dpg.set_value(self.log_viewer.ui_ids['log_text'],
                f"No logfile found for {selected_date.strftime('%B %d, %Y')}\n\n"
                        f"Expected file: {filepath}\n\n"
                        f"This could mean:\n"
                        f"• No keylogging data was recorded on this date\n"
                        f"• The log file hasn't been created yet \n"
                        f"• The keylogger wasn't running on this date"
                          )
            dpg.set_value(self.log_viewer.ui_ids['date_label'],
                          f"Log for: {selected_date.strftime('%B %d, %Y')}"
                          )
            dpg.set_value(self.log_viewer.ui_ids['info_label'],
                          "No log file found")
            dpg.configure_item(self.log_viewer.ui_ids['info_label'], color=(255, 165, 0))


    def _refresh_viewer(self, sender, app_data, user_data):
        """Refresh the current viewer"""
        if self.keylogger.is_running:
            # Load today's log
            today = datetime.datetime.now()
            self.log_viewer.load_file(
                self.file_manager.get_log_filename(today),
                self.file_manager
            )
        else:
            # Just refresh current
            self.log_viewer.refresh_current(self.file_manager)





    def _on_search_changed(self, sender, app_data, user_data):
        """Handle search text change"""
        search_text = dpg.get_value(sender)
        self.file_tree.populate(search_text)

    def _on_file_selected(self, filepath):
        """Handle file selection from tree"""
        print(f"Selected file: {filepath}")
        self.log_viewer.load_file(filepath, self.file_manager)
        # Will connect to log viewer later

    def _on_file_deleted(self, filepath):
        """Handle file deletion"""
        print(f"Deleted file: {filepath}")
        if self.log_viewer.current_filepath == filepath:
            self.log_viewer.clear()
        # Will connect viewer later



    def _build_right_panel(self):
        """Build right panel: status, log viewer"""

        # Status header
        self._build_status_header()


        dpg.add_separator()
        dpg.add_spacer(height=5)

        # Log viewer
        with dpg.group(tag="log_viewer_container"):
            pass

        self.log_viewer = LogViewerWidget("log_viewer_container")
        with dpg.group(horizontal=True):
            dpg.add_text("Ready", tag="status_bar_text", color=(150, 150, 150))
            dpg.add_spacer(width=20)

            # Show file count
            file_count = len(glob.glob("keylogs/keylog_*.txt"))
            dpg.add_text(f"Files: {file_count}", tag="file_count_text")



    def _build_status_header(self):
        """Build status header"""
        with dpg.group(horizontal=True):
            dpg.add_text("Status:", color=(200, 200, 200))
            self.ui_ids['status_label'] = dpg.add_text(
                "Ready",
                 color=(255, 165, 0) # Orange
            )

            dpg.add_spacer(width=20)
            dpg.add_text("|", color =(100, 100, 100))
            dpg.add_spacer(width=20)

            dpg.add_text("Tracking:", color=(200, 200, 200))
            self.ui_ids['executable_label'] = dpg.add_text(
                "Not running",
                color=(100, 150, 255)
            )

    def _update_loop(self):
        """Called every frame - checks for updates"""
        current_time = time.time()

        # Only update every 2 seconds
        if current_time - self.last_update_time >= 2.0:
            self.last_update_time = current_time
            self._update_status()

    def _update_status(self):
        """Update status and refresh data"""

        if not self.keylogger.is_running:
            dpg.set_value(self.ui_ids['executable_label'], "Not running")
            return  # Don't update if not running


        if self.keylogger.is_running:
            # Update tracking label
            try:
                self.current_executable = self.get_active_window()
                dpg.set_value(self.ui_ids['executable_label'], self.current_executable)

            except:
                dpg.set_value(self.ui_ids['executable_label'], "Unknown")

            # Refresh file tree
            search_text = dpg.get_value(self.ui_ids['search_input']) if 'search_input' in self.ui_ids else "" # ternary operator / Conditional Expression
            self.file_tree.populate(search_text)

            # Auto-refresh viewer if showing today's log
            if self.log_viewer.current_filepath:
                today_log = self.file_manager.get_log_filename()
                if self.log_viewer.current_filepath == today_log:
                    self.log_viewer.refresh_current(self.file_manager)
        else:
            dpg.set_value(self.ui_ids['executable_label'], "Not running")

        # Update file count
        file_count = len(glob.glob("keylogs/keylog_*.txt"))
        dpg.set_value("file_count_text", f"Files: {file_count}")


    def _create_button_themes(self):
        """Create custom button themes"""

        # Green theme for Start Button
        with dpg.theme(tag="green_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (16, 124, 16))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (20, 150, 20))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (12, 100, 12))

            # Red theme for Stop button
            with dpg.theme(tag="red_button_theme"):
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 16, 16))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 20, 20))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (170, 12, 12))
