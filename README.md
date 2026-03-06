# Keylogger with Viewer
**v2.1 — Storage Monitor Edition**

A Python desktop application for keystroke recording and log file management.

---

## Overview

Keylogger with Viewer is a cross-platform desktop application that captures and stores keystrokes, then lets you browse and review log files through a clean, Windows 11-style GUI built with Dear PyGui. It records which application was active during typing and organizes logs by date for easy retrieval.

---

## Features

- Real-time keystroke capture using pynput
- Active window tracking — shows which app was in focus
- Date-organized file tree (Month > Day > Year)
- Built-in log viewer with search and date picker
- Storage indicator showing current file size (KB / MB)
- Auto-scroll toggle for live monitoring
- Right-click context menu: Open or Delete files
- Windows 11-style dark theme
- Cross-platform: Windows, macOS, Linux

---

## Project Structure

| File | Description |
|------|-------------|
| `main.py` | Entry point — initializes DearPyGui and runs the app loop |
| `KeyloggerEngine.py` | Captures keystrokes via pynput; runs in background thread |
| `LogFileManager.py` | Handles file I/O: read, write, delete, organize log files |
| `PlatformUtils.py` | Platform detection for active window tracking (Win/Mac/Linux) |
| `UI_Components/KeyloggerViewerApp.py` | Main UI controller — builds layout, handles events |
| `UI_Components/FileTreeWidget.py` | Scrollable file tree with right-click menu |
| `UI_Components/LogViewerWidget.py` | Right panel log viewer with storage indicator |
| `UI_Components/ThemeManager.py` | Applies global dark theme to all DearPyGui components |

---

## Requirements

**Python 3.7 or higher**

| Package | Purpose | Install |
|---------|---------|---------|
| `dearpygui` | GPU-accelerated GUI framework | `pip install dearpygui` |
| `pynput` | Keyboard event capture | `pip install pynput` |
| `pywin32` | Active window detection (Windows only) | `pip install pywin32` |
| `psutil` | Process info for window tracking (Windows) | `pip install psutil` |
| `pyobjc-framework-Cocoa` | Active window detection (macOS only) | `pip install pyobjc-framework-Cocoa` |
| `xdotool` | Active window detection (Linux only) | `sudo apt install xdotool` |

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/keylogger-viewer.git
cd keylogger-viewer
```

### 2. Install Python dependencies
```bash
pip install dearpygui pynput
```

### 3. Install platform-specific packages

**Windows**
```bash
pip install pywin32 psutil
```

**macOS**
```bash
pip install pyobjc-framework-Cocoa
```

**Linux**
```bash
sudo apt install xdotool
```

### 4. Run the application
```bash
python main.py
```

---

## How It Works

### Architecture

The application uses a producer-consumer threading pattern:

- `KeyloggerEngine` runs in a background daemon thread and writes keystrokes to disk.
- It pushes the log file path onto a thread-safe `Queue` whenever a key is pressed.
- The main UI loop (`KeyloggerViewerApp._update_loop`) polls that queue every frame and refreshes the viewer only when new data arrives for the currently viewed file.
- This keeps the GUI responsive — the UI thread never blocks on I/O.

### Log File Format

Logs are stored in a `keylogs/` directory as plain text files named by date:

```
keylogs/keylog_YYYY-MM-DD.txt
```

Inside each file, entries are grouped by active window:

```
[--- Chrome.exe - GitHub --- 2025-03-06 14:22:01 ---]
Hello world<enter>
```

---

## Usage

| Action | How |
|--------|-----|
| Start logging | Click the green **Start Logging** button |
| Stop logging | Click the red **Stop Logging** button |
| View a log file | Click any file in the File Tree (left panel) |
| Load by date | Use the date picker, then click **Load Selected Date** |
| Search files | Type in the Search box to filter the file tree |
| Delete a file | Right-click a file in the tree > Delete |
| Refresh current view | Click **Refresh Current** or press `F5` |
| Toggle auto-scroll | Check/uncheck **Auto-scroll** (useful for live monitoring) |

---

## Storage & File Management

- Logs are written to `keylogs/` in the application directory.
- Each day gets one file. Starting the logger mid-day appends to the existing file.
- The storage indicator (top of the viewer) shows the size of the currently viewed file.
- Color coding: 🔵 blue = normal (<100 KB), 🟠 orange = moderate (<512 KB), 🔴 red = large (512 KB+).
- Files can be deleted from within the app via right-click > Delete.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Refresh the current log viewer |

---

## Platform Notes

### Windows
- Full feature support including active window name + executable.
- Requires `pywin32` and `psutil` for window tracking.

### macOS
- Active window tracking shows application name only (no window title).
- Requires `pyobjc-framework-Cocoa`.
- You may need to grant Accessibility permissions in **System Preferences > Privacy & Security**.

### Linux
- Requires `xdotool` for active window detection.
- May require running under an X11 session (not Wayland) for xdotool to work.

---

## Known Limitations

- The file tree rebuilds on every change — may be slow with hundreds of log files.
- Log viewer loads the entire file into memory; very large files (>10 MB) may be slow.
- On Linux under Wayland, active window detection will return `"Unknown"`.

---

## Disclaimer

> This software is intended for personal use on your own devices only. Recording keystrokes on a device without the owner's explicit consent may be illegal in your jurisdiction. The author assumes no responsibility for misuse.

---

## License

MIT License — free for personal and educational use.
