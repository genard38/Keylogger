import datetime
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class LogViewerWidget(QWidget):
    """
    PyQt6 equivalent of the DearPyGui LogViewerWidget.

    DPG approach: flat tag-based system — widgets are global IDs (ui_ids dict)
    PyQt6 approach: OOP — widgets are instance variables on self

    Key concept: In PyQt6, every widget is an OBJECT with methods.
    Instead of dpg.set_value(tag, value), you call widget.setText(value).
    Instead of dpg.configure_item(tag, color=...), you call widget.setStyleSheet(...)
    """

    def __init__(self, parent=None):
        # MUST call parent __init__ — like super() in Java inheritance
        super().__init__(parent)

        self.current_filepath = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """
        Build the widget layout.

        DPG used nested context managers (with dpg.group():)
        PyQt6 uses Layout objects — you add widgets INTO layouts,
        then set the layout on the parent widget.

        Layout types:
            QVBoxLayout  →  dpg.group()               (vertical stack)
            QHBoxLayout  →  dpg.group(horizontal=True) (horizontal stack)
        """
        # Root layout — everything stacks vertically
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(4)

        # ── Header row: Storage | Viewing ──────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        # "Storage:" label — static, never changes
        lbl_storage_title = QLabel("Storage:")
        lbl_storage_title.setStyleSheet("color: #c8c8c8;")

        # Storage VALUE label — updated dynamically via update_storage()
        # Equivalent to: dpg.add_text("0 KB", tag="storage_label")
        self.lbl_storage = QLabel("0 KB")
        self.lbl_storage.setStyleSheet("color: #96c8ff;")
        self.lbl_storage.setToolTip("Storage used by currently viewed file")

        # Pipe separator
        pipe1 = QLabel("|")
        pipe1.setStyleSheet("color: #646464;")

        lbl_viewing_title = QLabel("Viewing:")
        lbl_viewing_title.setStyleSheet("color: #c8c8c8;")

        # Date/filename VALUE label — updated when a file is loaded
        self.lbl_date = QLabel("No file selected")
        self.lbl_date.setStyleSheet("color: #969696;")

        # Add all header items left-to-right
        header.addWidget(lbl_storage_title)
        header.addWidget(self.lbl_storage)
        header.addSpacing(16)
        header.addWidget(pipe1)
        header.addSpacing(16)
        header.addWidget(lbl_viewing_title)
        header.addWidget(self.lbl_date)
        header.addStretch()  # pushes everything left (like dpg.add_spacer with fill)

        root_layout.addLayout(header)

        # ── Separator line ──────────────────────────────────────────────
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)   # dpg.add_separator()
        root_layout.addWidget(separator)

        # ── Main text area ──────────────────────────────────────────────
        # QTextEdit = dpg.add_input_text(multiline=True, readonly=True)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        # Monospace font — important for keylog readability
        self.text_edit.setFontFamily("Consolas")
        self.text_edit.setFontPointSize(10)

        # stretch=1 means this widget expands to fill remaining space
        # equivalent to height=-1 in dpg (fill parent)
        root_layout.addWidget(self.text_edit, stretch=1)

        # ── Info / status label at bottom ───────────────────────────────
        # dpg.add_text("Select a file...", tag="info_label")
        self.lbl_info = QLabel("Select a file to view logs")
        self.lbl_info.setStyleSheet("color: #9696ff;")
        root_layout.addWidget(self.lbl_info)

    # ------------------------------------------------------------------
    # Public API — same interface as the dpg version
    # ------------------------------------------------------------------

    def load_file(self, filepath, file_manager):
        """
        Load and display a log file.

        Changes vs dpg version:
        - No tag lookups (dpg.set_value / dpg.configure_item)
        - Direct method calls on widget references
        - self.lbl_date.setText(...)  instead of  dpg.set_value(ui_ids['date_label'], ...)
        - self.lbl_date.setStyleSheet(...)  instead of  dpg.configure_item(..., color=(...))
        """
        self.current_filepath = filepath
        filename = os.path.basename(filepath)

        # Show loading state
        self.lbl_info.setText("Loading...")
        self.lbl_info.setStyleSheet("color: #ffff00;")

        # Parse and display the date
        try:
            date_part = filename.replace("keylog_", "").replace(".txt", "")
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            date_str = date_obj.strftime("%B %d, %Y")
            self.lbl_date.setText(date_str)
            self.lbl_date.setStyleSheet("color: #64c8ff;")
        except ValueError:
            self.lbl_date.setText(filename)
            self.lbl_date.setStyleSheet("color: #969696;")

        # Load content
        try:
            content = file_manager.read_file(filepath)
            self.update_content(content)
            self.set_auto_scroll(False)  # Manual load = no auto scroll

            self.lbl_info.setText(f"Loaded: {filename}")
            self.lbl_info.setStyleSheet("color: #00ff00;")
        except Exception as e:
            self.update_content(f"Error reading file: {str(e)}")
            self.lbl_info.setText(str(e))
            self.lbl_info.setStyleSheet("color: #ff0000;")

    def update_content(self, content: str):
        """
        Update the text displayed in the viewer.

        DPG: dpg.set_value(ui_ids['log_text'], content)
        PyQt6: self.text_edit.setPlainText(content)

        setPlainText() is faster than setText() for large content
        because it skips HTML parsing.
        """
        self.text_edit.setPlainText(content)

    def set_auto_scroll(self, enabled: bool):
        """
        Enable or disable auto-scrolling to the bottom.

        DPG used tracked=True / track_offset=1.0 — a dpg-specific hack.
        PyQt6 uses the scrollbar's setValue() directly.

        QScrollBar.maximum() = the very bottom position.
        """
        if enabled:
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_storage(self, formatted_size: str, color: tuple):
        """
        Update the storage indicator label.

        Args:
            formatted_size: e.g. "125.3 KB"
            color: RGB tuple e.g. (150, 200, 255)

        Color conversion:
            DPG used RGB tuples: (150, 200, 255)
            QSS uses hex strings: #96c8ff
            We convert with Python's format spec: f"#{r:02x}{g:02x}{b:02x}"
        """
        r, g, b = color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.lbl_storage.setText(formatted_size)
        self.lbl_storage.setStyleSheet(f"color: {hex_color};")

    def refresh_current(self, file_manager):
        """Refresh the currently displayed file."""
        if self.current_filepath:
            self.load_file(self.current_filepath, file_manager)

    def clear(self):
        """
        Clear the viewer — called when a file is deleted.
        Resets all labels back to default state.
        """
        self.current_filepath = None
        self.text_edit.clear()
        self.lbl_date.setText("File deleted")
        self.lbl_date.setStyleSheet("color: #ff6464;")
        self.lbl_info.setText("")