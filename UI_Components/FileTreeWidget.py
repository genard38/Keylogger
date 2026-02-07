#FileTreeWidget_dpg.py
from fileinput import filename

import dearpygui.dearpygui as dpg
import os

class FileTreeWidget:
    """File tree widget - Dear PyGui version"""

    MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    # Windows 11 style icons
    ICON_FOLDER = "📁"
    ICON_FILE = "📄"


    def __init__(self, parent_id, file_manager):
        self.parent_id = parent_id
        self.file_manager = file_manager
        self.file_tree_items = {} # ID -> filepath mapping
        self.on_file_selected = None # Callback
        self.on_file_deleted = None # Callback


        self._create_widget()

    def _create_widget(self, tree_window=None):
        """Create the tree widget inside a child window"""
        # Child window provides scrolling
        with dpg.child_window(
            height=300,
            parent=self.parent_id,
            tag="file_tree_window"
        ):
            # Tree will be populated here
            dpg.add_text("File tree loading...", tag="tree_placeholder")

        with dpg.tooltip("file_tree_window"):
            dpg.add_text("Double-click: Open file")
            dpg.add_text("Right-click: Options menu")
            dpg.add_text("Expand folders to see log files", color=(150, 150, 150))

        # Create shared right-click handler registry
        with dpg.item_handler_registry(tag="file_item_handler"):
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right, callback=self._handle_right_click)

    def populate(self, filter_text=""):
        """Populate the tree with files"""
        # Get new data
        organized = self.file_manager.organize_files()

        # Check if changed (simple hash comparison)
        new_hash = hash(str(organized))
        if hasattr(self, '_last_hash') and self._last_hash == new_hash and filter_text == self._last_filter:
            return #No changes , skip rebuild

        self._last_hash = new_hash
        self._last_filter = filter_text

        # Delete existing tree content
        if dpg.does_item_exist("tree_placeholder"):
            dpg.delete_item("tree_placeholder")

        # Delete all existing tree nodes
        children = dpg.get_item_children("file_tree_window", slot=1)
        if children:
            for child in children:
                dpg.delete_item(child)

        # Add temporary loading text (Add this AFTER clearing children)
        if not dpg.does_item_exist("tree_loading_indicator"):
            dpg.add_text("Loading files...", tag="tree_loading_indicator", parent="file_tree_window",
                         color=(255, 255, 0))

        # Clear mapping
        self.file_tree_items.clear()

        # Get organized files
        organized = self.file_manager.organize_files()

        # Build tree
        with dpg.group(parent="file_tree_window"):
            for month in self.MONTH_ORDER:
                if month not in organized:
                    continue

                # Filter logic
                if filter_text and not self._matches_filter(month, organized[month], filter_text):
                    continue

                # Create month node
                with dpg.tree_node(label=f"{self.ICON_FOLDER} {month}", default_open=False):

                    # Sort day
                    days = sorted(organized[month].keys(), key=lambda x: int(x))

                    for day in days:
                        # Create day node
                        with dpg.tree_node(label=f"{self.ICON_FILE} keylog_day_{day}.txt", default_open=False):

                            # Sort years
                            years_files = sorted(organized[month][day], key=lambda x: x[0], reverse=True)

                            for year, filepath in years_files:
                                # Filter individual files
                                display_text = f"{month} {day} {year}"
                                if filter_text and filter_text.lower() not in display_text.lower():
                                    continue

                                # Create selectable file item
                                file_id = dpg.add_selectable(
                                    label=f"{self.ICON_FILE} {year}",
                                    callback=self._on_file_click,
                                    user_data=filepath
                                )

                                # Bind right-click handler
                                dpg.bind_item_handler_registry(file_id, "file_item_handler")

                                # Store mapping
                                self.file_tree_items[file_id] = filepath

        # Right before the method ends, add:
        if dpg.does_item_exist("tree_loading_indicator"):
            dpg.delete_item("tree_loading_indicator")
        # ===================================================================



    def _matches_filter(self, month, days_dict, filter_text):
        """Check if month/days match filter"""
        if not filter_text:
            return True
        if filter_text.lower() in month.lower():
            return True
        for day in days_dict:
            for year, _ in days_dict[day]:
                if filter_text.lower() in f"{month} {day} {year}".lower():
                    return True
        return False


    def _on_file_click(self, sender, app_data, user_data):
        """Handle file selection"""
        filepath = user_data # We passed filepath as user_data
        if self.on_file_selected:
            self.on_file_selected(filepath)

    def _handle_right_click(self, sender, app_data):
        """Handle right click on file item"""
        # app_data is (clicked_item_id, button_index)
        clicked_item = app_data[1]
        self._show_context_menu(clicked_item, None)

    def _show_context_menu(self, sender, app_data):
        """Show right-click context menu"""

        # Get clicked item
        if sender not in self.file_tree_items:
            return

        filepath = self.file_tree_items[sender]

        # Create popup window
        if dpg.does_item_exist("file_context_menu"):
            dpg.delete_item("file_context_menu")

        with dpg.window(
            label="File Options",
            modal=True,
            show=True,
            tag="file_context_menu",
            pos=dpg.get_mouse_pos(local=False),
            no_title_bar=True,
            autosize=True
        ):
            dpg.add_button(
                label="Open",
                callback=lambda: self._context_open(filepath),
                width=150
            )
            dpg.add_button(
                label="Delete",
                callback=lambda: self._context_delete(filepath),
                width=150
            )
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item("file_context_menu"),
                width=150
            )

    def _context_open(self, filepath):
        """Open file from context menu"""
        dpg.delete_item("file_context_menu")
        if self.on_file_selected:
            self.on_file_selected(filepath)

    def _context_delete(self, filepath):
        """Delete file from context menu"""
        dpg.delete_item("file_context_menu")

        # Confirm dialog
        if dpg.does_item_exist("confirm_delete"):
            dpg.delete_item("confirm_delete")

        with dpg.window(
            label="Confirm Delete",
            modal=True,
            show=True,
            tag="confirm_delete",
            autosize=True,
            pos=(400, 300)
        ):
            dpg.add_text(f"Delete {os.path.basename(filepath)}?")
            dpg.add_text("This cannot be undone.", color=(225, 100, 100))
            dpg.add_spacer(height=10)

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes, Delete",
                    callback=lambda: self._do_delete(filepath),
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item("confirm_delete"),
                    width=100
                )

    def _do_delete(self, filepath):
        """Actually delete the file"""
        dpg.delete_item("confirm_delete")

        try:
            self.file_manager.delete_file(filepath)
            self.populate() # Refresh tree
            if self.on_file_deleted:
                self.on_file_deleted(filepath)
        except Exception as e:
            # Error dialog
            with dpg.window(label="Error", modal=True, show=True, autosize=True):
                dpg.add_text(f"Failed to delete: {str(e)}", color=(255, 0, 0))
                dpg.add_button(label="OK", callback=lambda s, a: dpg.delete_item(dpg.get_item_parent(s)))
