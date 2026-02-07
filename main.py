
import dearpygui.dearpygui as dpg
from UI_Components.KeyloggerViewerApp import KeyloggerViewerApp
from UI_Components.ThemeManager import ThemeManager

def main():
    # Create context
    dpg.create_context()

    # Apply theme
    ThemeManager.setup_theme()
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