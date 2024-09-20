import plotly.graph_objects as pgo
import json
import networkx as nx
import random
from datetime import datetime

from core.internal_rest_apis import _get_universe_by_name, _get_region_metadata
from core.map_functions import center_on_view


def get_diagram_map(customer_uuid: str, universe_name: str):

    # UNIVERSE
    # retrieve info about the universe from various REST APIs
    # see https://api-docs.yugabyte.com

    ## get availability zones for this universe
    universe_info = _get_universe_by_name(customer_uuid, universe_name)
    node_details = universe_info[0]["universeDetails"]["nodeDetailsSet"]

    node_dict = {}

    for i, node in enumerate(node_details):
        node_dict[f"node_{i}"] = {
            "cloud": node["cloudInfo"]["cloud"],
            "region": node["cloudInfo"]["region"],
            "az": node["cloudInfo"]["az"],
            "private_ip": node["cloudInfo"]["private_ip"],
        }

    ## get region metadata for this universe, to include longitude and latitude
    ## transform the lat/long slightly so the servers in a single region don't overlap
    ## update node dictionary with this long/lat
    for node_key, node_data in node_dict.items():
        cloud_metadata = _get_region_metadata(customer_uuid, node_data["cloud"])[
            "regionMetadata"
        ][node_data["region"]]
        node_data["latitude"] = cloud_metadata["latitude"] + random.uniform(0.001, 0.05)
        node_data["longitude"] = cloud_metadata["longitude"] + random.uniform(
            0.001, 0.05
        )

    # NODES
    # extract node geographical positions for graph
    # (nodes = database instances in the universe)

    ## this includes the node coordinates (longitude, latitude)
    node_positions = {}

    node_positions = {
        node_data["az"]: (node_data["longitude"], node_data["latitude"])
        for node_data in node_dict.values()
    }

    # EDGES
    # extract edge endpoint pairs for graph
    # (edge = network connections between database instances)
    edge_endpoints = []

    az_list = [node_data["az"] for node_data in node_dict.values()]
    edge_endpoints = [(az_list[i], az_list[i + 1]) for i in range(len(az_list) - 1)]
    edge_endpoints.append((az_list[-1], az_list[0]))  # add the final edge

    # GRAPH

    ## create a network graph
    G = nx.Graph()

    ## add nodes and edge endpoints (both of which are the AZ names) to graph object
    G.add_nodes_from(node_positions.keys())
    G.add_edges_from(edge_endpoints)

    ## get longitude and latitude for node placement
    node_longitudes = [node_positions[node][0] for node in G.nodes()]
    node_latitudes = [node_positions[node][1] for node in G.nodes()]

    ## get longitude and latitude for edge endpoint placement
    edge_longitudes = []
    edge_latitudes = []
    for edge in G.edges():
        lon0, lat0 = node_positions[edge[0]]
        lon1, lat1 = node_positions[edge[1]]

        edge_longitudes.append(lon0)
        edge_longitudes.append(lon1)
        edge_longitudes.append(None)
        # 'None' is used to break the line between segments

        edge_latitudes.append(lat0)
        edge_latitudes.append(lat1)
        edge_latitudes.append(None)

    ## create the node trace (trace = drawing on the map)
    node_trace = pgo.Scattermapbox(
        lon=node_longitudes,
        lat=node_latitudes,
        mode="markers+text",
        marker=dict(size=10, color="blue"),
        text=list(G.nodes()),  # display the server names as text
        hoverinfo="text",
    )

    ## create the edge trace
    edge_trace = pgo.Scattermapbox(
        lon=edge_longitudes,
        lat=edge_latitudes,
        mode="lines",
        line=dict(width=2, color="DarkSlateGrey"),
        hoverinfo="none",
    )

    ## create the Mapbox figure
    ## center_on_view helps to center and zoom on the bounding box of the universe
    average_latitude, average_longitude, calculated_zoom = center_on_view(
        node_latitudes, node_longitudes
    )

    current_time = datetime.now()
    display_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    fig = pgo.Figure(
        data=[edge_trace, node_trace],
        layout=pgo.Layout(
            title=f"YugabyteDB node distribution for {universe_name} {display_time}",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            mapbox=dict(
                style="open-street-map",  # see https://docs.mapbox.com/mapbox-gl-js/guides/styles/
                center=dict(
                    lat=average_latitude,  # center on average latitude
                    lon=average_longitude,  # center on average longitude
                ),
                zoom=calculated_zoom,
            ),
        ),
    )

    # OUTPUT

    ## get timestamp for universe details and mapbox html files
    file_time = current_time.strftime("%Y%m%d_%H:%M:%S")

    ## save the full node details to a file
    file_name = f"/tmp/{universe_name}-{file_time}"

    with open(file_name, "w") as file:
        file.write(json.dumps(universe_info, indent=4))
    print(f"Contents written to {file_name}")

    ## save the mapbox as an html file
    fig.write_html(f"/tmp/{universe_name}-{file_time}.html")
    print(f"plot saved to {universe_name}-{file_time}.html")

    ## alternatively immediately open figure in the default browser
    # fig.show()
