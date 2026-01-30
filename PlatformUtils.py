import platform


class PlatformUtils:
    """Handle platform-specific operations for window detection"""


    @staticmethod
    def setup_platform_libraries():
        """Import platform-specific libraries and set up window detection"""
        if platform.system() == "Windows":
            return PlatformUtils._setup_windows()
        elif platform.system() == "Darwin":
            return PlatformUtils._setup_macos()
        elif platform.system() == "Linux":
            return PlatformUtils._setup_linux()
        else:
            return lambda: "Unsupported OS"

    @staticmethod
    def _setup_windows():
        try:
            import win32gui
            import win32process
            import psutil

            def get_active_window():
                try:
                    window = win32gui.GetForegroundWindow()
                    pid = win32process.GetWindowThreadProcessId(window)[1]
                    process = psutil.Process(pid)
                    window_title = win32gui.GetWindowText(window)
                    return f"{process.name()} - {window_title}"
                except:
                    return "Unknown"

            return get_active_window
        except ImportError:
            print("Warning: pywin32 and psutil not installed. Install with: pip install pywin32 psutil")
            return lambda: "N/A (libraries not installed)"

    @staticmethod
    def _setup_macos():
        try:
            from AppKit import NSWorkspace

            def get_active_window():
                try:
                    active_app = NSWorkspace.sharedWorkspace().activeApplication()
                    return f"{active_app['NSApplicationName']}"
                except:
                    return "Unknown"

            return get_active_window
        except ImportError:
            print("Warning: pyobjc not installed. Install with: pip install pyobjc-framework-Cocoa")
            return lambda: "N/A (libraries not installed)"

    @staticmethod
    def _setup_linux():
        import subprocess

        def get_active_window():
            try:
                window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
                window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
                return window_name
            except:
                return "Unknown"

        return get_active_window