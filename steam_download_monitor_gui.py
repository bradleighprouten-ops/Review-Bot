#!/usr/bin/env python3
"""Simple GUI wrapper for the Steam download monitor."""
from __future__ import annotations

import argparse
import threading
import tkinter as tk
from tkinter import ttk

from steam_download_monitor import run_monitor_from_args


class MonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Steam Download Monitor")
        self.status_var = tk.StringVar(value="Ready.")

        self._build_form()

    def _build_form(self) -> None:
        padding = {"padx": 10, "pady": 5}

        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Steam root (optional):").grid(row=0, column=0, sticky="w", **padding)
        self.steam_root_entry = ttk.Entry(frame, width=50)
        self.steam_root_entry.grid(row=0, column=1, sticky="ew", **padding)

        ttk.Label(frame, text="AppID (optional):").grid(row=1, column=0, sticky="w", **padding)
        self.appid_entry = ttk.Entry(frame, width=20)
        self.appid_entry.grid(row=1, column=1, sticky="w", **padding)

        ttk.Label(frame, text="Poll seconds:").grid(row=2, column=0, sticky="w", **padding)
        self.poll_seconds_entry = ttk.Entry(frame, width=10)
        self.poll_seconds_entry.insert(0, "10")
        self.poll_seconds_entry.grid(row=2, column=1, sticky="w", **padding)

        self.require_log_var = tk.BooleanVar(value=False)
        self.shutdown_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            frame,
            text="Require content_log confirmation",
            variable=self.require_log_var,
        ).grid(row=3, column=0, columnspan=2, sticky="w", **padding)

        ttk.Checkbutton(
            frame,
            text="Shutdown when complete",
            variable=self.shutdown_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", **padding)

        self.start_button = ttk.Button(frame, text="Start Monitor", command=self._start_monitor)
        self.start_button.grid(row=5, column=0, columnspan=2, **padding)

        ttk.Label(frame, textvariable=self.status_var).grid(row=6, column=0, columnspan=2, sticky="w", **padding)

        frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _start_monitor(self) -> None:
        args = argparse.Namespace(
            steam_root=self._clean_entry(self.steam_root_entry),
            appid=self._clean_entry(self.appid_entry),
            poll_seconds=self._parse_poll_seconds(),
            require_log=self.require_log_var.get(),
            shutdown=self.shutdown_var.get(),
        )

        self.status_var.set("Monitoring started. Keep this window open.")
        self.start_button.configure(state="disabled")

        thread = threading.Thread(target=run_monitor_from_args, args=(args,), daemon=True)
        thread.start()

    def _clean_entry(self, entry: ttk.Entry) -> str | None:
        value = entry.get().strip()
        return value or None

    def _parse_poll_seconds(self) -> int:
        raw = self.poll_seconds_entry.get().strip()
        if not raw:
            return 10
        if raw.isdigit():
            return max(1, int(raw))
        return 10


def main() -> None:
    root = tk.Tk()
    MonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
