
from PyQt6.QtWidgets import QApplication


class ThemeManager:
    #@staticmethod
    """
    PyQt6 equivalent of the DearPyGui Theme Manager.
    
    DPG. used: dpg.theme() + dpg.add_theme_color() + dpg.bind_theme()
    PyQt6 uses: QSS (Qt Style Sheets) - like CSS but for the Qt widgets
    
    QSS Selector syntax:
        QPushButton         → targets ALL QPushButton widgets
        QPushButton:hover   → targets hovered state (like CSS :hover)
        QPushButton#myId    → targets widget with setObjectName("myId")
    """

    # Windows 11-inspired dark theme colors (same values as your dpg version)
    COLORS = {
        "bg_dark": "#1e1e1e",  # (30, 30, 30)  - main window bg
        "bg_medium": "#282828",  # (40, 40, 40)  - child panels
        "bg_light": "#323232",  # (50, 50, 50)  - inputs, frames
        "bg_hover": "#464646",  # (70, 70, 70)  - hover state
        "bg_active": "#505050",  # (80, 80, 80)  - active/pressed
        "border": "#3c3c3c",  # (60, 60, 60)  - borders
        "accent_blue": "#0078d7",  # (0, 120, 215) - Windows blue
        "accent_hover": "#008ceb",  # (0, 140, 235)
        "accent_active": "#0064c3",  # (0, 100, 195)
        "text_primary": "#dcdcdc",  # (220, 220, 220)
        "text_muted": "#969696",  # (150, 150, 150)
        "text_blue": "#6496ff",  # (100, 150, 255)
        "green": "#107c10",  # Start button green
        "red": "#c81010",  # Stop button red
    }

    @staticmethod
    def setup_theme(app: QApplication):
        """
        Apply the global stylesheet to the QApplication.
        This is equivalent to dpg.bind_theme(global_theme).

        Args:
            app: the QApplication instance (must exist before calling this)
        :param app:
        :return:
        """
        stylesheet = ThemeManager._build_stylesheet()
        app.setStyleSheet(stylesheet)


    def get_button_style(color: str) -> str:
        """
        Return inline QSS for a specific button color.
        Used for the green Start / red Stop buttons.

        Args:
            color: "green" or "red"

        Returns:
            str. QSS string to pass widget.setStyleSheet()
        """
        c = ThemeManager.COLORS
        bg = c["green"] if color == "green" else c["red"]

        return f"""
                    QPushButton {{
                        background-color: {bg};
                        color: {c['text_primary']};
                        border: none;
                        padding: 6px 8px;
                        border-radius: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: {bg}cc;
                    }}
                    QPushButton:disabled {{
                        background-color: {c['bg_light']};
                        color: {c['text_muted']};
                    }}
                """

    @staticmethod
    def _build_stylesheet() -> str:
        """
        Build the full QSS stylesheet string.

        Think of this like a CSS file — one place controls all styling.
        The f-string pulls from COLORS dict so magic numbers only appear once.
        """
        c = ThemeManager.COLORS

        return f"""
                /* ── Main Window ── */
                QMainWindow, QWidget {{
                    background-color: {c['bg_dark']};
                    color: {c['text_primary']};
                    font-size: 13px;
                }}

                /* ── Child panels / frames ── */
                QFrame, QGroupBox {{
                    background-color: {c['bg_medium']};
                    border: 1px solid {c['border']};
                    border: none;
                    border-radius: 5px;
                }}

                /* ── Buttons ── */
                QPushButton {{
                    background-color: {c['accent_blue']};
                    color: {c['text_primary']};
                    border: none;
                    padding: 6px 8px;
                    border-radius: 5px;
                    min-height: 24px;
                }}
                QPushButton:hover {{
                    background-color: {c['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {c['accent_active']};
                }}
                QPushButton:disabled {{
                    background-color: {c['bg_light']};
                    color: {c['text_muted']};
                }}

                /* ── Text inputs ── */
                QLineEdit, QTextEdit, QPlainTextEdit {{
                    background-color: {c['bg_light']};
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    border-radius: 5px;
                    padding: 4px 6px;
                }}
                QLineEdit:focus, QTextEdit:focus {{
                    border: 1px solid {c['accent_blue']};
                }}

                /* ── Tree widget ── */
                QTreeWidget {{
                    background-color: {c['bg_medium']};
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    border-radius: 5px;
                }}
                QTreeWidget::item:hover {{
                    background-color: {c['bg_hover']};
                }}
                QTreeWidget::item:selected {{
                    background-color: {c['accent_blue']};
                    color: white;
                }}
                QTreeWidget::branch {{
                    background-color: {c['bg_medium']};
                }}

                /* ── Scrollbars ── */
                QScrollBar:vertical {{
                    background: {c['bg_medium']};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background: {c['bg_hover']};
                    border-radius: 5px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {c['text_muted']};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}

                /* ── Menu bar ── */
                QMenuBar {{
                    background-color: {c['bg_dark']};
                    color: {c['text_primary']};
                    border-bottom: 1px solid {c['border']};
                }}
                QMenuBar::item:selected {{
                    background-color: {c['accent_blue']};
                }}
                QMenu {{
                    background-color: {c['bg_medium']};
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                }}
                QMenu::item:selected {{
                    background-color: {c['accent_blue']};
                }}

                /* ── Separator lines ── */
                QFrame[frameShape="4"],
                QFrame[frameShape="5"] {{
                    background-color: {c['border']};
                    border: none;
                    max-height: 1px;
                }}

                /* ── Labels ── */
                QLabel {{
                    background-color: transparent;
                    border: none;
                }}

                /* ── Calendar widget ── */
                QCalendarWidget QAbstractItemView {{
                    background-color: {c['bg_medium']};
                    color: {c['text_primary']};
                    selection-background-color: {c['accent_blue']};
                }}
                QCalendarWidget QWidget#qt_calendar_navigationbar {{
                    background-color: {c['bg_dark']};
                }}

                /* ── Splitter handle ── */
                QSplitter::handle {{
                    background-color: {c['border']};
                }}

                /* ── Dialog / modal windows ── */
                QDialog {{
                    background-color: {c['bg_dark']};
                    color: {c['text_primary']};
                }}

                /* ── Tooltips ── */
                QToolTip {{
                    background-color: {c['bg_medium']};
                    color: {c['text_primary']};
                    border: 1px solid {c['accent_blue']};
                    padding: 4px;
                    border-radius: 3px;
                }}

                /* ── Checkbox ── */
                QCheckBox {{
                    color: {c['text_primary']};
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {c['border']};
                    border-radius: 3px;
                    background-color: {c['bg_light']};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {c['accent_blue']};
                    border-color: {c['accent_blue']};
                }}

                /* ── Status bar ── */
                QStatusBar {{
                    background-color: {c['bg_dark']};
                    color: {c['text_muted']};
                    border-top: 1px solid {c['border']};
                }}
            """











