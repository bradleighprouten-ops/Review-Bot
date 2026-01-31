#!/usr/bin/env python3
"""Monitor Steam download completion by checking local Steam files."""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_POLL_SECONDS = 10


@dataclass(frozen=True)
class SteamPaths:
    root: Path
    steamapps: Path
    downloading: Path
    content_log: Path


def _default_root_candidates() -> list[Path]:
    home = Path.home()
    candidates: list[Path] = []

    if sys.platform.startswith("win"):
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        if program_files_x86:
            candidates.append(Path(program_files_x86) / "Steam")
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(Path(program_files) / "Steam")
        candidates.append(home / "AppData" / "Local" / "Steam")
    elif sys.platform == "darwin":
        candidates.append(home / "Library" / "Application Support" / "Steam")
    else:
        candidates.append(home / ".steam" / "steam")
        candidates.append(home / ".local" / "share" / "Steam")

    return candidates


def resolve_steam_paths(root_override: str | None) -> SteamPaths:
    if root_override:
        root = Path(root_override).expanduser().resolve()
        return _steam_paths_from_root(root)

    for candidate in _default_root_candidates():
        if candidate.exists():
            return _steam_paths_from_root(candidate)

    raise FileNotFoundError(
        "Could not locate Steam install. Use --steam-root to provide the path."
    )


def _steam_paths_from_root(root: Path) -> SteamPaths:
    steamapps = root / "steamapps"
    downloading = steamapps / "downloading"
    content_log = root / "logs" / "content_log.txt"
    return SteamPaths(root=root, steamapps=steamapps, downloading=downloading, content_log=content_log)


def list_active_downloads(downloading_dir: Path) -> list[str]:
    if not downloading_dir.exists():
        return []

    active = []
    for child in downloading_dir.iterdir():
        if not child.is_dir():
            continue
        has_files = any(child.iterdir())
        if has_files:
            active.append(child.name)
    return sorted(active)


def appmanifest_path(steamapps: Path, appid: str) -> Path:
    return steamapps / f"appmanifest_{appid}.acf"


def read_last_log_lines(content_log: Path, limit: int = 120) -> list[str]:
    if not content_log.exists():
        return []
    try:
        with content_log.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
        return [line.strip() for line in lines[-limit:]]
    except OSError:
        return []


def log_mentions_completion(lines: Iterable[str], appid: str | None) -> bool:
    keywords = ("Finished", "fully installed", "installed", "update complete")
    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in keywords):
            if appid is None or appid in line:
                return True
    return False


def is_download_complete(paths: SteamPaths, appid: str | None) -> bool:
    active = list_active_downloads(paths.downloading)
    if appid:
        if appid in active:
            return False
        manifest = appmanifest_path(paths.steamapps, appid)
        if manifest.exists():
            return True
        return False

    return len(active) == 0


def summarize_state(paths: SteamPaths, appid: str | None) -> str:
    active = list_active_downloads(paths.downloading)
    if appid:
        if appid in active:
            return f"AppID {appid} is downloading (active downloads: {', '.join(active)})."
        return f"AppID {appid} not present in active downloads."
    if active:
        return f"Active downloads: {', '.join(active)}."
    return "No active downloads detected."


def shutdown_computer() -> None:
    if sys.platform.startswith("win"):
        os.system("shutdown /s /t 0")
        return
    if sys.platform == "darwin":
        os.system("sudo shutdown -h now")
        return
    os.system("shutdown -h now")


def monitor_download(
    paths: SteamPaths,
    appid: str | None,
    poll_seconds: int,
    require_log: bool,
    shutdown_on_complete: bool,
) -> int:
    print(f"Monitoring Steam root: {paths.root}")
    if appid:
        print(f"Watching AppID: {appid}")
    else:
        print("Watching all downloads.")

    while True:
        if is_download_complete(paths, appid):
            if require_log:
                lines = read_last_log_lines(paths.content_log)
                if log_mentions_completion(lines, appid):
                    print("Download complete (confirmed by content log).")
                    if shutdown_on_complete:
                        print("Shutting down computer.")
                        shutdown_computer()
                    return 0
                print("No completion entry found in content log yet.")
            else:
                print("Download complete.")
                if shutdown_on_complete:
                    print("Shutting down computer.")
                    shutdown_computer()
                return 0

        print(summarize_state(paths, appid))
        time.sleep(poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor Steam download completion by inspecting local files.",
    )
    parser.add_argument(
        "--steam-root",
        help="Path to Steam installation root (if auto-detection fails).",
    )
    parser.add_argument(
        "--appid",
        help="Optional AppID to track a single download.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=DEFAULT_POLL_SECONDS,
        help=f"Polling interval in seconds (default: {DEFAULT_POLL_SECONDS}).",
    )
    parser.add_argument(
        "--require-log",
        action="store_true",
        help="Require a completion line in content_log.txt before exiting.",
    )
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Shut down the computer when the download is complete.",
    )
    return parser.parse_args()


def run_monitor_from_args(args: argparse.Namespace) -> int:
    try:
        paths = resolve_steam_paths(args.steam_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return monitor_download(
        paths=paths,
        appid=args.appid,
        poll_seconds=max(1, args.poll_seconds),
        require_log=args.require_log,
        shutdown_on_complete=args.shutdown,
    )


def main() -> int:
    args = parse_args()
    return run_monitor_from_args(args)


if __name__ == "__main__":
    raise SystemExit(main())
