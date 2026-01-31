import dearpygui.dearpygui as dpg

class ThemeManager:
    @staticmethod
    def setup_theme():
        """Create and apply Windows 11-like dark theme"""

        with dpg.theme() as global_theme:

            with dpg.theme_component(dpg.mvAll):
                # Colors
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30))  # Dark background
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (40, 40, 40))  # Slightly lighter
                dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 60, 60))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (80, 80, 80))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (20, 20, 20))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (30, 30, 30))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 120, 215))  # Windows blue
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 140, 235))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 100, 195))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 120, 215))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (0, 140, 235))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (0, 100, 195))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220))

                # Styling
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)

        dpg.bind_theme(global_theme)
