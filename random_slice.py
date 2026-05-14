"""Pick a random zoomed bounding box for the 'random' display mode.

The slice is sized to roughly match the Reterminal's 800x480 aspect
ratio (5:3), in degrees: ~0.04 deg of longitude by ~0.024 deg of
latitude. At Austin's latitude that's a little under 4 km by 2.6 km.
"""

from __future__ import annotations

import random

import geopandas as gpd

Bbox = tuple[float, float, float, float]

# Default slice size in degrees (lon, lat). 5:3 aspect ratio.
SLICE_LON = 0.04
SLICE_LAT = 0.024

# Capital Metro service area bounds (WGS84) — fallback when no vehicles.
SYSTEM_BOUNDS: Bbox = (-97.9921, 30.1403, -97.3701, 30.5958)


def _bbox_around(lon: float, lat: float) -> Bbox:
    half_lon = SLICE_LON / 2
    half_lat = SLICE_LAT / 2
    return (lon - half_lon, lat - half_lat, lon + half_lon, lat + half_lat)


def pick_bbox(vehicles: gpd.GeoDataFrame | None = None) -> Bbox:
    """Return a random bbox, preferring one centered on an active vehicle.

    If ``vehicles`` is empty or ``None``, fall back to a random point
    inside the system bounds.
    """
    if vehicles is not None and not vehicles.empty:
        row = vehicles.sample(n=1).iloc[0]
        return _bbox_around(float(row["lon"]), float(row["lat"]))

    minx, miny, maxx, maxy = SYSTEM_BOUNDS
    # Keep the slice fully inside the system bounds.
    lon = random.uniform(minx + SLICE_LON / 2, maxx - SLICE_LON / 2)
    lat = random.uniform(miny + SLICE_LAT / 2, maxy - SLICE_LAT / 2)
    return _bbox_around(lon, lat)
