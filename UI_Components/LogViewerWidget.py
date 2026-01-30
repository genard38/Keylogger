

import dearpygui.dearpygui as dpg
import datetime
import os

class LogViewerWidget:
    """Long viewer widget - Dear PyGui version"""

    def __init__(self, parent_id):
        self.parent_id = parent_id
        self.current_filepath = None
        self.ui_ids = {}

        self._create_widget()


    def _create_widget(self):
        """Create the viewer widget"""
        with dpg.group(parent=self.parent_id):


            # Date label
            self.ui_ids['date_label'] = dpg.add_text(
                "No date selected",
                color = (200, 200, 255)
            )

            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Log content viewer (scrollable)
            with dpg.child_window(height=-40):  # -40 leaves room for info label
                self.ui_ids['log_text'] = dpg.add_input_text(
                    multiline=True,         # Multiple lines
                    readonly=True,          # Can't edit
                    width=-1,               # FIX: Use -1 to fill parent width
                    height=-1,              # FIX: Use -1 to fill parent height
                    tab_input=True          # Tab creates tab character instead of changing focus
                )

            dpg.add_spacer(height=5)

            # Info label at bottom (MOVED outside the child window)
            self.ui_ids['info_label'] = dpg.add_text(
                "Select a file to view logs",
                color=(150, 150, 255)
            )

    def load_file(self, filepath, file_manager):
        """Load and display a log file"""
        self.current_filepath = filepath
        filename = os.path.basename(filepath)

        # === Show loading indicator ===
        dpg.set_value(self.ui_ids['info_label'], "Loading...")
        dpg.configure_item(self.ui_ids['info_label'], color=(255, 255, 0))  # Yellow
        # =========================================


        # Update date label
        try:
            date_part = filename.replace("keylog_","").replace(".txt","")
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            date_str = date_obj.strftime("%B %d, %Y")
            dpg.set_value(self.ui_ids['date_label'],f"Log for: {date_str}")
        except:
            dpg.set_value(self.ui_ids['date_label'], f"Log for: {filename}")

        # Load content
        try:
            content = file_manager.read_file(filepath)
            dpg.set_value(self.ui_ids['log_text'], content)

            dpg.set_value(self.ui_ids['info_label'], f"Loaded: {filename}")
            dpg.configure_item(self.ui_ids['info_label'], color=(0,255,0))
        except Exception  as e:
            error_msg = f"Error reading file: {str(e)}"
            dpg.set_value(self.ui_ids['log_text'], error_msg)
            dpg.set_value(self.ui_ids['info_label'], str(e))
            dpg.configure_item(self.ui_ids['info_label'], color=(255,0,0))

    def refresh_current(self, file_manager):
        """Refresh the currently displayed file"""
        if self.current_filepath:
            self.load_file(self.current_filepath, file_manager)

    def clear(self):
        """Clear the viewer"""
        self.current_filepath = None
        dpg.set_value(self.ui_ids['log_text'], "")
        dpg.set_value(self.ui_ids['date_label'], "File deleted")
        dpg.set_value(self.ui_ids['info_label'], "")
