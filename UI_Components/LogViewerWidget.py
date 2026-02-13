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
            # Replace "No date selected" with storage indicator header
            with dpg.group(horizontal=True):
                dpg.add_text("Storage:", color=(200, 200, 200))
                self.ui_ids['storage_label'] = dpg.add_text("0 KB", color=(150, 200, 255))
                with dpg.tooltip(self.ui_ids['storage_label']):
                    dpg.add_text("Storage used by currently viewed file")

                dpg.add_spacer(width=30)
                dpg.add_text("|", color=(100, 100, 100))
                dpg.add_spacer(width=30)

                dpg.add_text("Viewing:", color=(200, 200, 200))
                self.ui_ids['date_label'] = dpg.add_text("No file selected", color=(150, 150, 150))

            dpg.add_separator()
            dpg.add_spacer(height=5)

            self.ui_ids['log_container'] = dpg.generate_uuid()
            # Enable horizontal scrollbar on the container
            with dpg.child_window(height=-40, tag=self.ui_ids['log_container'], horizontal_scrollbar=True):
                self.ui_ids['log_text'] = dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    width=2000, # Large width to enable horizontal scrolling
                    height=-1,  # Fill parent container
                    tab_input=True
                )
                # Add a spacer at the bottom to ensure the last line is fully visible when scrolling to bottom
                dpg.add_spacer(height=20)

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
            dpg.set_value(self.ui_ids['date_label'], date_str)
            dpg.configure_item(self.ui_ids['date_label'], color=(100, 200, 255))
        except:
            dpg.set_value(self.ui_ids['date_label'], filename)
            dpg.configure_item(self.ui_ids['date_label'], color=(150, 150, 150))

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
        # Disable tracking on the text widget itself to prevent horizontal jumping
        dpg.configure_item(self.ui_ids['log_text'], tracked=False)
        
        if enabled:
            # Scroll the container (child window) to the bottom vertically
            # We use a large number to ensure we hit the bottom
            dpg.set_y_scroll(self.ui_ids['log_container'], 999999.0)

    def update_storage(self, formatted_size: str, color: tuple):
        """Update the storage indicator display."""
        if 'storage_label' in self.ui_ids:
            dpg.set_value(self.ui_ids['storage_label'], formatted_size)
            dpg.configure_item(self.ui_ids['storage_label'], color=color)

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
        dpg.configure_item(self.ui_ids['date_label'], color=(255, 100, 100))
        dpg.set_value(self.ui_ids['info_label'], "")