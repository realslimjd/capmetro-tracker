from create_routes import RouteType
from create_map import CreateMap

class AustinRouteTypes(RouteType):
    HIGH_FREQUENCY = "High Frequency"
    UT_SHUTTLE = "UT Shuttle"
    CROSSTOWN = "Crosstown"
    LOCAL = "Local"
    FEEDER = "Feeder"
    NIGHT_OWL = "Night Owl"
    RAIL = "Rail"
    FLYER = "Flyer"
    SPECIAL = "Special"
    EXPRESS = "Express"


AUSTIN_ROUTE_COLORS = {
    AustinRouteTypes.HIGH_FREQUENCY: '#FFC0CB',  # pink
    AustinRouteTypes.UT_SHUTTLE: '#BF5700',      # burnt orange
    AustinRouteTypes.CROSSTOWN: '#008000',       # green
    AustinRouteTypes.LOCAL: '#008080',           # teal
    AustinRouteTypes.FEEDER: '#800080',          # purple
    AustinRouteTypes.NIGHT_OWL: '#000080',       # navy blue
    AustinRouteTypes.RAIL: '#FF0000',            # red
    AustinRouteTypes.FLYER: '#D3D3D3',           # light gray
    AustinRouteTypes.SPECIAL: '#FFFF00',         # yellow
    AustinRouteTypes.EXPRESS: '#A9A9A9',         # dark gray
}

class AustinMap(CreateMap):
    route_filename = 'Capital_Metro_Shapefiles_-_AUGUST_2022/Routes.shp'
    # This is the download URL which is different than the landing page for the data
    vehicle_location_url = 'https://data.texas.gov/download/cuc7-ywmd/text%2Fplain'
    vehicle_location_filename = 'vehiclepositions.json'
    route_types = AustinRouteTypes
    route_colors = AUSTIN_ROUTE_COLORS


austin = AustinMap()
austin.create_plot()
