import logging

import geopandas as gpd
import matplotlib.pyplot as plt
import requests

import create_routes
import create_vehicles
from create_routes import RouteType

logger = logging.getLogger(__name__)


class CreateMap:
    route_filename: str
    vehicle_location_url: str
    vehicle_location_filename: str
    route_types: type[RouteType]
    route_colors: dict[RouteType, str]

    def fetch_vehicle_position_file(self) -> None:
        response = requests.get(self.vehicle_location_url)
        response.raise_for_status()
        with open(self.vehicle_location_filename, "wb") as file:
            file.write(response.content)

    def create_route_dataframe(self) -> gpd.GeoDataFrame:
        routes = create_routes.generate_route_info(
            self.route_filename, self.route_types, self.route_colors
        )

        return routes

    def create_vehicle_location_dataframe(
        self, refresh_positions: bool = True
    ) -> gpd.GeoDataFrame:
        if refresh_positions:
            self.fetch_vehicle_position_file()

        vehicles = create_vehicles.create_vehicle_location_dataframe(
            self.vehicle_location_filename
        )

        return vehicles

    def create_plot(self) -> None:
        fig, ax = plt.subplots(figsize=(15, 15))

        routes = self.create_route_dataframe()
        routes.plot(
            ax=ax, color=routes["color"], linewidth=1.5, alpha=0.6, label="Routes"
        )

        vehicles = self.create_vehicle_location_dataframe()
        vehicles.plot(ax=ax, color="red", markersize=20, marker="o", label="Vehicles")

        ax.axis("off")
        plt.title("Capital Metro Routes And Vehicle Locations")
        # For some reason the png doesn't generate an image if we show() it first
        # plt.show()
        plt.savefig("routes_test.png", dpi=300, bbox_inches="tight")
