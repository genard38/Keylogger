# Keylogger with Viewer

A Python desktop application that records keystrokes to daily log files and provides a real-time viewer UI built with PyQt6.

---

## Features

- **Start / Stop logging** — toggle keystroke capture at any time
- **Active window tracking** — each log entry is grouped by the application in focus
- **Daily log files** — logs are saved as `keylogs/keylog_YYYY-MM-DD.txt`
- **Real-time viewer** — the UI refreshes automatically while logging is active
- **File tree** — browse all saved logs organized by Month → Day → Year
- **Calendar picker** — jump to any date's log file directly
- **Search / filter** — filter the file tree by date string
- **File management** — delete log files from the right-click context menu
- **Storage indicator** — shows file size of the currently viewed log
- **Auto-scroll** — checkbox to follow live output as keys are logged
- **Cross-platform** — Windows, macOS, and Linux supported

---

## Project Structure

```
Keylogger with Viewer/
│
├── main.py                          # Entry point — creates QApplication and launches window
│
├── KeyloggerEngine.py               # Keystroke capture logic (pynput listener)
├── LogFileManager.py                # File I/O: create, read, write, delete log files
├── PlatformUtils.py                 # OS-specific active window detection
│
├── UI_Components/
│   ├── KeyloggerViewerApp.py        # Main window — layout, signals, periodic updates
│   ├── FileTreeWidget.py            # Left panel tree: browse log files
│   ├── LogViewerWidget.py           # Right panel: display log content
│   └── ThemeManager.py             # Dark theme stylesheet (QSS)
│
├── backup_tkinter/                  # Old Tkinter version (kept for reference)
│
├── keylogs/                         # Auto-created — stores all log files
│   └── keylog_YYYY-MM-DD.txt
│
└── requirements.txt
```

---

## Requirements

- Python 3.7+
- Windows: `pywin32`, `psutil` (for active window detection)
- macOS: `pyobjc-framework-Cocoa`
- Linux: `xdotool` (system package)

Install Python dependencies:

```bash
pip install -r requirements.txt
pip install PyQt6 pynput
```

> On Windows, also run:
> ```bash
> pip install pywin32 psutil
> ```

---

## Running the App

```bash
python main.py
```

---

## How It Works

### Keystroke Capture (`KeyloggerEngine`)
- Uses `pynput.keyboard.Listener` running in a background thread
- On each keypress, checks if the active window changed — if so, writes a section header
- Appends each key as a character or `<special_key>` tag to the daily log file
- Notifies the UI via a thread-safe signal queue

### Log Files (`LogFileManager`)
- One `.txt` file per day: `keylogs/keylog_2026-01-08.txt`
- All writes are protected by a `threading.Lock` to prevent race conditions
- `organize_files()` parses filenames and returns a `{ month: { day: [(year, path)] } }` structure

### UI (`KeyloggerViewerApp`)
- Built with **PyQt6** — replaces an earlier DearPyGui and Tkinter version
- `QSplitter` divides the window into a left panel (controls + file tree) and right panel (log viewer)
- A `QTimer` fires every 2 seconds to refresh the active window label and file tree
- Thread-safe UI updates use a custom `_SignalQueue` adapter that wraps a `pyqtSignal`

### Active Window Detection (`PlatformUtils`)
| OS      | Method                                      |
|---------|---------------------------------------------|
| Windows | `win32gui` + `psutil`                       |
| macOS   | `NSWorkspace` via `pyobjc`                  |
| Linux   | `xdotool getactivewindow` subprocess call   |

---

## Log File Format

Newer logs (Feb 2026+) use a compact inline format:

```
[--- Logging Started: 2026-03-09 08:59:05 ---]

[--- msedge.exe - New tab --- 2026-03-09 08:59:24 ---]
monkeytype.com<enter>

[--- claude.exe - Claude --- 2026-03-09 09:06:06 ---]
generate<space>a<space>commit<space>message<enter>
```

Older logs (Jan 2026) use a verbose per-key format where each keystroke is on its own timestamped line.

---

## Privacy Notice

This tool logs **all keystrokes** including passwords and personal messages. It is intended for personal productivity tracking or parental monitoring on your own devices only. Do not use it on any device without the explicit consent of the user being monitored.
