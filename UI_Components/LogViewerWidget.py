
import dearpygui.dearpygui as dpg
import datetime
import os

class LogViewerWidget:
    """Log viewer widget - Dear PyGui version"""

    def __init__(self, parent_id):
        self.parent_id = parent_id
        self.current_filepath = None
        self.ui_ids = {}
        self._create_widget()

    def _create_widget(self):
        """Create the viewer widget"""
        with dpg.group(parent=self.parent_id):
            self.ui_ids['date_label'] = dpg.add_text("No date selected", color=(200, 200, 255))
            dpg.add_separator()
            dpg.add_spacer(height=5)

            self.ui_ids['log_container'] = dpg.generate_uuid()
            with dpg.child_window(height=-40, tag=self.ui_ids['log_container']):
                self.ui_ids['log_text'] = dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=-1,  # Fill parent container
                    tab_input=True
                )

            dpg.add_spacer(height=5)
            self.ui_ids['info_label'] = dpg.add_text("Select a file to view logs", color=(150, 150, 255))

    def load_file(self, filepath, file_manager):
        """Load and display a log file, disabling auto-scroll."""
        self.current_filepath = filepath
        filename = os.path.basename(filepath)

        dpg.set_value(self.ui_ids['info_label'], "Loading...")
        dpg.configure_item(self.ui_ids['info_label'], color=(255, 255, 0))

        try:
            date_part = filename.replace("keylog_", "").replace(".txt", "")
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            date_str = date_obj.strftime("%B %d, %Y")
            dpg.set_value(self.ui_ids['date_label'], f"Log for: {date_str}")
        except:
            dpg.set_value(self.ui_ids['date_label'], f"Log for: {filename}")

        try:
            content = file_manager.read_file(filepath)
            self.update_content(content)
            self.set_auto_scroll(False)  # Manual load should not auto-scroll

            dpg.set_value(self.ui_ids['info_label'], f"Loaded: {filename}")
            dpg.configure_item(self.ui_ids['info_label'], color=(0, 255, 0))
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.update_content(error_msg)
            dpg.set_value(self.ui_ids['info_label'], str(e))
            dpg.configure_item(self.ui_ids['info_label'], color=(255, 0, 0))

    def update_content(self, content: str):
        """Updates the text content of the log viewer."""
        dpg.set_value(self.ui_ids['log_text'], content)

    def set_auto_scroll(self, enabled: bool):
        """Enables or disables auto-scrolling to the bottom."""
        if enabled:
            # This toggle sequence is more robust for forcing a state update.
            dpg.configure_item(self.ui_ids['log_text'], tracked=False)
            dpg.configure_item(self.ui_ids['log_text'], tracked=True, track_offset=1.0)
        else:
            dpg.configure_item(self.ui_ids['log_text'], tracked=False)

    def refresh_current(self, file_manager):
        """Refresh the currently displayed file."""
        if not self.current_filepath:
            return

        self.load_file(self.current_filepath, file_manager)

    def clear(self):
        """Clear the viewer."""
        self.current_filepath = None
        self.update_content("")
        dpg.set_value(self.ui_ids['date_label'], "File deleted")
        dpg.set_value(self.ui_ids['info_label'], "")
