from dataclasses import dataclass
from enum import Enum
import geopandas as gpd


class RouteType(Enum):
    pass


@dataclass
# This is probably redundant
class Route:
    name: str
    color: str
    type: RouteType


def color_routes(
    routes_latlon: gpd.GeoDataFrame,
    local_route_types: type[RouteType],
    route_colors: dict[RouteType, str],
) -> gpd.GeoDataFrame:
    def get_route_color(route_type_str):
        if route_type_str is None:
            return "#808080"  # gray for unknown routes

        for route_type in local_route_types:
            if route_type.value == route_type_str:
                return route_colors.get(route_type, "#808080")

        return "#808080"  # gray for unknown routes

    routes_latlon["color"] = routes_latlon["ROUTETYPE"].apply(get_route_color)
    return routes_latlon


def generate_route_info(
    route_filename: str,
    route_types: type[RouteType],
    route_colors: dict[RouteType, str],
) -> gpd.GeoDataFrame:
    routes = gpd.read_file(route_filename)
    routes_latlon = routes.to_crs(epsg=4326)
    routes_latlon = color_routes(routes_latlon, route_types, route_colors)

    return routes_latlon
