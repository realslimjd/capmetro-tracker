"""Polling client for the Reterminal E1002.

Every 60 s, fetches /image from the configured server, writes it to
``/tmp/transit.png``, and (optionally) re-spawns a fullscreen viewer
to show it. The simplest setup is to launch ``feh --reload 60`` once
separately and let this script just keep overwriting the file — feh
will pick the new image up automatically.

Configuration (environment variables):
    SERVER_URL    e.g. http://192.168.1.42:5000   (required)
    MODE          full | line | random            (default: full)
    ROUTE_ID      int, required if MODE=line
    POLL_SECONDS  override the 60 s interval      (default: 60)
    OUTPUT_PATH   where to write the PNG          (default: /tmp/transit.png)
    VIEWER        "feh" | "fbi" | "none"          (default: none)
                  - "feh"  : assume feh is already running with --reload;
                             this script just overwrites the file.
                  - "fbi"  : kill+respawn fbi each tick (framebuffer).
                  - "none" : just write the file; you arrange display.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("transit-display")


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def env_required(name: str) -> str:
    val = os.environ.get(name)
    if val is None or not val:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(2)
    assert val is not None
    return val


def build_url(server: str, mode: str, route_id: str | None) -> str:
    server = server.rstrip("/")
    if mode == "line":
        return f"{server}/image?mode=line&route_id={route_id}"
    return f"{server}/image?mode={mode}"


def fetch_image(url: str, dest: Path, timeout: float = 30.0) -> bool:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Fetch failed: %s", exc)
        return False
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(resp.content)
    tmp.replace(dest)  # atomic swap so viewers never see a half-written file
    logger.info("Wrote %d bytes to %s", len(resp.content), dest)
    return True


def respawn_fbi(image_path: Path, current_pid: int | None) -> int | None:
    """Kill any previous fbi we started, spawn a fresh one. Returns new pid."""
    if current_pid is not None:
        try:
            os.kill(current_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        proc = subprocess.Popen(
            ["fbi", "-T", "1", "-noverbose", "-a", str(image_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc.pid
    except FileNotFoundError:
        logger.error("fbi not found on PATH; install it or set VIEWER=none")
        return None


def main() -> int:
    server = env_required("SERVER_URL")
    mode = (env("MODE", "full") or "full").lower()
    route_id = env("ROUTE_ID")
    poll_seconds = int(env("POLL_SECONDS", "60") or "60")
    output_path = Path(env("OUTPUT_PATH", "/tmp/transit.png") or "/tmp/transit.png")
    viewer = (env("VIEWER", "none") or "none").lower()

    if mode == "line" and not route_id:
        logger.error("MODE=line requires ROUTE_ID")
        return 2

    url = build_url(server, mode, route_id)
    logger.info(
        "Polling %s every %ds, writing to %s (viewer=%s)",
        url,
        poll_seconds,
        output_path,
        viewer,
    )

    fbi_pid: int | None = None

    while True:
        ok = fetch_image(url, output_path)
        if ok and viewer == "fbi":
            fbi_pid = respawn_fbi(output_path, fbi_pid)
        # viewer="feh" needs no action — feh --reload watches the file.
        # viewer="none" — nothing to do.
        time.sleep(poll_seconds)


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(130)
