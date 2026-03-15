import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QDialog, QDialogButtonBox,
    QLabel, QVBoxLayout as QVBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon


class FileTreeWidget(QWidget):
    """
    PyQt6 equivalent of the DearPyGui FileTreeWidget.

    DPG approach:
        - Built tree by creating dpg.tree_node() items manually
        - Right-click via item_handler_registry
        - Callbacks via user_data on each selectable

    PyQt6 approach:
        - QTreeWidget manages the whole tree
        - Right-click via customContextMenuRequested signal
        - Data stored directly on QTreeWidgetItem via setData()

    Key concept — Signals & Slots (replaces dpg callbacks):
        DPG:    dpg.add_selectable(callback=my_func, user_data=filepath)
        PyQt6:  widget.signal.connect(my_slot)
                where signal = event source, slot = handler function

    Custom signals (defined at class level, not in __init__):
        These replace your on_file_selected / on_file_deleted callback attributes.
        Any code can connect to them: self.file_tree.file_selected.connect(my_func)
    """

    # Class-level signal declarations — equivalent to your callback attributes:
    #   self.on_file_selected = None  →  file_selected = pyqtSignal(str)
    #   self.on_file_deleted  = None  →  file_deleted  = pyqtSignal(str)
    # The (str) means the signal carries one string argument (the filepath)
    file_selected = pyqtSignal(str)
    file_deleted = pyqtSignal(str)

    MONTH_ORDER = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    ICON_FOLDER = "📁"
    ICON_FILE   = "📄"

    def __init__(self, parent=None, file_manager=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self._last_hash = None
        self._last_filter = ""
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # QTreeWidget = the whole tree component
        # In dpg you manually built tree_node() items inside a child_window.
        # Here QTreeWidget manages expand/collapse, selection, scrolling itself.
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)       # No column header — same as dpg
        self.tree.setAnimated(True)           # Smooth expand/collapse

        # Right-click menu setup:
        # CustomContextMenu = "I'll handle right-clicks myself"
        # When right-clicked, Qt fires the customContextMenuRequested signal
        # We connect that signal to our handler method
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_right_click)

        # Single-click to select/open file
        # itemClicked signal fires when user clicks any item
        self.tree.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.tree)

        # Tooltip on the tree container
        self.tree.setToolTip(
            "Click: Open file\n"
            "Right-click: Options menu\n"
            "Expand folders to see log files"
        )

    # ------------------------------------------------------------------
    # Tree Population
    # ------------------------------------------------------------------

    def populate(self, filter_text=""):
        """
        Populate the tree with log files.

        DPG version deleted all children then rebuilt from scratch using
        dpg.delete_item() on each child.

        PyQt6 version uses tree.clear() — one call wipes everything,
        then we rebuild with QTreeWidgetItem objects.
        """
        organized = self.file_manager.organize_files()

        # Skip rebuild if nothing changed (same optimization as dpg version)
        new_hash = hash(str(organized))
        if self._last_hash == new_hash and filter_text == self._last_filter:
            return
        self._last_hash = new_hash
        self._last_filter = filter_text

        # Wipe existing tree — equivalent to deleting all dpg children
        self.tree.clear()

        for month in self.MONTH_ORDER:
            if month not in organized:
                continue
            if filter_text and not self._matches_filter(month, organized[month], filter_text):
                continue

            # ── Month node (top level) ──────────────────────────────────
            # QTreeWidgetItem(self.tree) = add to root = dpg.tree_node() at top level
            month_item = QTreeWidgetItem(self.tree)
            month_item.setText(0, f"{self.ICON_FOLDER} {month}")

            # Sort days numerically (same logic as dpg version)
            days = sorted(organized[month].keys(), key=lambda x: int(x))

            for day in days:
                # ── Day node (second level) ─────────────────────────────
                # QTreeWidgetItem(month_item) = child of month = nested dpg.tree_node()
                day_item = QTreeWidgetItem(month_item)
                day_item.setText(0, f"{self.ICON_FILE} keylog_day_{day}.txt")

                years_files = sorted(organized[month][day], key=lambda x: x[0], reverse=True)

                for year, filepath in years_files:
                    display_text = f"{month} {day} {year}"
                    if filter_text and filter_text.lower() not in display_text.lower():
                        continue

                    # ── File leaf node (third level) ────────────────────
                    # This replaces dpg.add_selectable() + user_data=filepath
                    file_item = QTreeWidgetItem(day_item)
                    file_item.setText(0, f"{self.ICON_FILE} {year}")

                    # Store filepath directly ON the item using Qt's data system
                    # setData(column, role, value)
                    # Qt.ItemDataRole.UserRole = custom slot for your own data
                    # This replaces: self.file_tree_items[file_id] = filepath
                    file_item.setData(0, Qt.ItemDataRole.UserRole, filepath)

    # ------------------------------------------------------------------
    # Event Handlers (Slots)
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Handle single click on tree item.

        Replaces: dpg.add_selectable(callback=self._on_file_click, user_data=filepath)

        We retrieve the filepath using getData() — the reverse of setData().
        Non-file items (month/day nodes) have no UserRole data, so getData returns None.
        """
        filepath = item.data(0, Qt.ItemDataRole.UserRole)
        if filepath:
            # Emit signal — equivalent to: if self.on_file_selected: self.on_file_selected(filepath)
            # Anyone connected to this signal will be called automatically
            self.file_selected.emit(filepath)

    def _on_right_click(self, position):
        """
        Handle right-click — show context menu.

        DPG used item_handler_registry + dpg.window(modal=True).
        PyQt6 uses QMenu — a native context menu that auto-dismisses.

        position = coordinates within the tree widget (local coords)
        We convert to screen coords for menu placement.
        """
        # Get which item was right-clicked
        item = self.tree.itemAt(position)
        if not item:
            return

        filepath = item.data(0, Qt.ItemDataRole.UserRole)
        if not filepath:
            return  # Clicked a folder node, not a file

        # Build context menu — replaces dpg.window(modal=True) with buttons
        menu = QMenu(self)
        action_open   = menu.addAction("Open")
        action_delete = menu.addAction("Delete")

        # exec() shows the menu and BLOCKS until user clicks or dismisses
        # mapToGlobal converts local widget coords → screen coords
        chosen = menu.exec(self.tree.mapToGlobal(position))

        if chosen == action_open:
            self.file_selected.emit(filepath)
        elif chosen == action_delete:
            self._confirm_delete(filepath)

    # ------------------------------------------------------------------
    # Delete Flow
    # ------------------------------------------------------------------

    def _confirm_delete(self, filepath):
        """
        Show confirmation dialog before deleting.

        DPG: dpg.window(modal=True) with manual buttons
        PyQt6: QMessageBox — a built-in standard dialog

        QMessageBox.StandardButton.Yes / No = the button choices
        """
        filename = os.path.basename(filepath)

        # QMessageBox is simpler than building a dpg modal window manually
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {filename}?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default highlighted button
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._do_delete(filepath)

    def _do_delete(self, filepath):
        """Execute the file deletion."""
        try:
            self.file_manager.delete_file(filepath)
            self.populate(self._last_filter)  # Refresh tree
            self.file_deleted.emit(filepath)   # Notify parent app
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete file:\n{str(e)}"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _matches_filter(self, month, days_dict, filter_text):
        """Check if month/days match the search filter — unchanged logic."""
        if not filter_text:
            return True
        if filter_text.lower() in month.lower():
            return True
        for day in days_dict:
            for year, _ in days_dict[day]:
                if filter_text.lower() in f"{month} {day} {year}".lower():
                    return True
        return False