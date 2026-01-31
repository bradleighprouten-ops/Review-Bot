# Review-Bot

## Steam download monitor (Option C)

This repo includes a small script that checks Steam's local download state instead
of reading the screen. It watches the `steamapps/downloading` folder and can
optionally confirm completion via `logs/content_log.txt`.

### CLI Usage

```bash
./steam_download_monitor.py --appid 261550
```

Common options:

```bash
./steam_download_monitor.py --steam-root "C:/Program Files (x86)/Steam" --require-log
./steam_download_monitor.py --poll-seconds 5
./steam_download_monitor.py --appid 261550 --shutdown
```

If Steam can't be auto-detected, pass `--steam-root` with your install path.
The `--shutdown` flag will attempt to power off the machine and may require
administrator privileges depending on your OS.

### GUI (Windows/macOS/Linux)

Run the GUI wrapper and click **Start Monitor**:

```bash
./steam_download_monitor_gui.py
```

### Build a Windows EXE

You can package the GUI into a standalone executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole steam_download_monitor_gui.py
```

The resulting EXE will be in `dist/steam_download_monitor_gui.exe`.
