import math


def center_on_view(latitudes_list, longitudes_list):

    # find the bounding box for all nodes
    latitude_range = max(latitudes_list) - min(latitudes_list)
    longitude_range = max(longitudes_list) - min(longitudes_list)

    # calculate the center of the bounding box
    center_latitude = (max(latitudes_list) + min(latitudes_list)) / 2
    center_longitude = (max(longitudes_list) + min(longitudes_list)) / 2

    # calculate the zoom level to include the bounding box
    max_range = max(
        max(latitude_range, longitude_range), 1e-6
    )  # avoid dividing by zero
    zoom = math.log2(360 / max_range)

    return center_latitude, center_longitude, zoom
