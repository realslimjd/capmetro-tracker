import geopandas as gpd
import json
from shapely.geometry import Point

def create_vehicle_location_dataframe(vehicle_location_filename: str) -> gpd.GeoDataFrame:
    """This reads from a GeoJSON file of vehicle locations and turns it into a GeoDataFrame"""
    with open(vehicle_location_filename, 'r') as f:
        data = json.load(f)

    vehicle_coords = []
    for entity in data['entity']:
      if 'vehicle' in entity and 'position' in entity['vehicle']:
          pos = entity['vehicle']['position']
          vehicle = entity['vehicle']

          # Extract route ID from trip data if available
          route_id = None
          if 'trip' in vehicle and 'routeId' in vehicle['trip']:
              route_id = vehicle['trip']['routeId']

          vehicle_coords.append({
              'id': entity['id'],
              'lat': pos['latitude'],
              'lon': pos['longitude'],
              'route_id': route_id,
              'geometry': Point(pos['longitude'], pos['latitude'])
          })

    vehicles_gdf = gpd.GeoDataFrame(vehicle_coords, crs='EPSG:4326')
    print(vehicles_gdf)

    return vehicles_gdf