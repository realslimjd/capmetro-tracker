import io
import logging
from typing import BinaryIO, Literal

import geopandas as gpd
import matplotlib.pyplot as plt
import requests

import create_routes
import create_vehicles
from create_routes import RouteType

logger = logging.getLogger(__name__)

Mode = Literal["full", "line", "random"]
Bbox = tuple[float, float, float, float]


class CreateMap:
    route_filename: str
    vehicle_location_url: str
    vehicle_location_filename: str
    route_types: type[RouteType]
    route_colors: dict[RouteType, str]

    # System-wide bounds for Capital Metro service area (WGS84). Used as a
    # fallback when we have no vehicles to anchor a random slice to.
    SYSTEM_BOUNDS: Bbox = (-97.9921, 30.1403, -97.3701, 30.5958)

    def fetch_vehicle_position_file(self) -> None:
        response = requests.get(self.vehicle_location_url, timeout=15)
        response.raise_for_status()
        with open(self.vehicle_location_filename, "wb") as file:
            file.write(response.content)

    def create_route_dataframe(self) -> gpd.GeoDataFrame:
        return create_routes.generate_route_info(
            self.route_filename, self.route_types, self.route_colors
        )

    def create_vehicle_location_dataframe(
        self, refresh_positions: bool = True
    ) -> gpd.GeoDataFrame:
        if refresh_positions:
            self.fetch_vehicle_position_file()

        return create_vehicles.create_vehicle_location_dataframe(
            self.vehicle_location_filename
        )

    def create_plot(
        self,
        mode: Mode = "full",
        route_id: int | None = None,
        bbox: Bbox | None = None,
        size_px: tuple[int, int] = (800, 480),
        out: BinaryIO | str = "routes_test.png",
        refresh_positions: bool = True,
    ) -> None:
        """Render the map to ``out`` (a file path or a binary stream).

        ``mode``:
            - ``"full"``  – entire system
            - ``"line"``  – a single route (requires ``route_id``)
            - ``"random"`` – a random zoomed slice, optionally with a
              caller-supplied ``bbox``. If ``bbox`` is ``None`` and mode
              is ``"random"``, the caller is expected to pass one in via
              ``bbox`` (the Flask server uses ``random_slice.pick_bbox``).

        ``size_px`` is honored exactly — we use ``figsize=size_px / dpi``
        with ``dpi=100`` and *do not* pass ``bbox_inches="tight"`` which
        would crop the result to content.
        """
        if mode == "line" and route_id is None:
            raise ValueError("route_id is required when mode='line'")

        dpi = 100
        width_in = size_px[0] / dpi
        height_in = size_px[1] / dpi
        fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)

        # Routes
        routes = self.create_route_dataframe()
        vehicles = self.create_vehicle_location_dataframe(refresh_positions)

        if mode == "line":
            assert route_id is not None  # validated above; narrows for type checker
            rid = int(route_id)
            routes = routes[routes["ROUTE_ID"] == rid]
            if not vehicles.empty:
                # vehicle route_id is a string in the GTFS-RT feed
                vehicles = vehicles[
                    vehicles["route_id"].fillna("-1").astype(int) == rid
                ]

        if not routes.empty:
            routes.plot(
                ax=ax,
                color=routes["color"],
                linewidth=1.5,
                alpha=0.6,
                label="Routes",
            )
        if not vehicles.empty:
            vehicles.plot(
                ax=ax, color="red", markersize=20, marker="o", label="Vehicles"
            )

        # Determine view extent
        view_bbox: Bbox | None = None
        if bbox is not None:
            view_bbox = bbox
        elif mode == "line" and not routes.empty:
            minx, miny, maxx, maxy = routes.total_bounds
            # 5% buffer on each side so the line isn't flush with the edge
            bx = (maxx - minx) * 0.05 or 0.01
            by = (maxy - miny) * 0.05 or 0.01
            view_bbox = (minx - bx, miny - by, maxx + bx, maxy + by)

        if view_bbox is not None:
            ax.set_xlim(view_bbox[0], view_bbox[2])
            ax.set_ylim(view_bbox[1], view_bbox[3])

        ax.axis("off")

        # Exact-pixel save: no tight bbox, no padding.
        if isinstance(out, (str, bytes)):
            fig.savefig(out, format="png", dpi=dpi, bbox_inches=None, pad_inches=0)
        else:
            fig.savefig(out, format="png", dpi=dpi, bbox_inches=None, pad_inches=0)
            if hasattr(out, "seek"):
                try:
                    out.seek(0)
                except (io.UnsupportedOperation, OSError):
                    pass

        plt.close(fig)
