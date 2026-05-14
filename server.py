"""Flask server: returns a freshly-rendered 800x480 PNG on every request.

Endpoints:
    GET /healthz                  -> 200 "ok"
    GET /image?mode=full
    GET /image?mode=line&route_id=<int>
    GET /image?mode=random

Run:
    uv run python server.py
    # or: flask --app server run --host 0.0.0.0 --port 5000
"""

from __future__ import annotations

# Force the non-GUI Agg backend before anything else imports matplotlib.
# Flask serves requests from worker threads and the default macOS backend
# refuses to create figures off the main thread.
import matplotlib

matplotlib.use("Agg")

import io  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402

from flask import Flask, Response, request, send_file  # noqa: E402

import random_slice
from austin_map import AustinMap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Instantiate once so the shapefile load (slow) happens at startup.
austin = AustinMap()


VALID_MODES = {"full", "line", "random"}


@app.get("/healthz")
def healthz() -> Response:
    return Response("ok", mimetype="text/plain")


@app.get("/image")
def image():
    mode = request.args.get("mode", "full").lower()
    if mode not in VALID_MODES:
        return Response(
            f"invalid mode '{mode}'. Must be one of: {sorted(VALID_MODES)}",
            status=400,
            mimetype="text/plain",
        )

    route_id_str = request.args.get("route_id")
    route_id: int | None = None
    if mode == "line":
        if route_id_str is None:
            return Response(
                "mode='line' requires route_id query parameter",
                status=400,
                mimetype="text/plain",
            )
        try:
            route_id = int(route_id_str)
        except ValueError:
            return Response(
                f"route_id must be an integer, got '{route_id_str}'",
                status=400,
                mimetype="text/plain",
            )

    # Pull fresh vehicle data once per request so both render + bbox use it.
    try:
        austin.fetch_vehicle_position_file()
    except Exception:  # noqa: BLE001 — keep serving even if upstream blips
        logger.exception("Failed to refresh vehicle positions; using cached file")

    bbox = None
    if mode == "random":
        vehicles = austin.create_vehicle_location_dataframe(refresh_positions=False)
        bbox = random_slice.pick_bbox(vehicles)

    buf = io.BytesIO()
    austin.create_plot(
        mode=mode,
        route_id=route_id,
        bbox=bbox,
        size_px=(800, 480),
        out=buf,
        refresh_positions=False,  # we already refreshed above
    )
    buf.seek(0)

    response = send_file(buf, mimetype="image/png")
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
