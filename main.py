
import dearpygui.dearpygui as dpg
import os
import ctypes
import platform
from UI_Components.KeyloggerViewerApp import KeyloggerViewerApp
from UI_Components.ThemeManager import ThemeManager

def main():
    # Enable High DPI awareness on Windows to fix zoomed/blurry UI
    if platform.system() == "Windows":
        try:
            # Set System DPI Awareness (1) instead of Per-Monitor (2) to maintain consistent size across monitors
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            # Fallback to System DPI Awareness (Windows Vista+)
            ctypes.windll.user32.SetProcessDPIAware()

    # Create context
    dpg.create_context()

    # Apply theme
    ThemeManager.setup_theme()

    # Load custom font to support Unicode icons (Play, Pause, Folder, File)
    with dpg.font_registry():
        # Try to locate a system font that supports emojis/symbols
        # Windows 10/11 usually has Segoe UI Emoji which supports all the icons used
        font_path = "C:/Windows/Fonts/seguiemj.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/segoeui.ttf" # Fallback to standard Segoe UI

        if os.path.exists(font_path):
            with dpg.font(font_path, 18) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                # Explicitly add the specific icons used in the app to ensure they load
                dpg.add_font_chars([
                    0x25B6, # ▶ Play
                    0x23F8, # ⏸ Pause
                    0x25BC, # ▼ Down Arrow
                    0x1F4C1, # 📁 Folder
                    0x1F4C4,  # 📄 File
                    0x1F504, # 🔄 Refresh
                    0x25B2 # ▲ Up Arrow
                ])
            dpg.bind_font(default_font)

    # Create app (this builds the UI)
    app = KeyloggerViewerApp()

    # 3. Setup viewport
    dpg.create_viewport(title="Keylogger with Viewer", width=1200, height=700)
    dpg.setup_dearpygui()

    # Set primary window
    dpg.set_primary_window("primary_window", True)

    # Show and start
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        app._update_loop()
        dpg.render_dearpygui_frame()

    # 6. Cleanup (runs after window closes)
    dpg.destroy_context()

if __name__ == "__main__":
    main()