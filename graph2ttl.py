import xml.etree.ElementTree as ET

import networkx as nx
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS
from shapely import Polygon
from shapely.geometry import LineString

# Define namespaces
OSM = Namespace("http://openstreetmap.org/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
EXT = Namespace("https://www.extract-project.eu/ontology#")
SF = Namespace("http://www.opengis.net/ont/sf#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
OTN = Namespace("http://www.pms.ifi.uni-muenchen.de/OTN#")

# Create a graph
rdf_graph = Graph()

# Parse the OSM XML file
tree = ET.parse('graph.graphml')
root = tree.getroot()

# Load the GraphML file
graphml_file_path = 'graph.graphml'
graph = nx.read_graphml(graphml_file_path)

# Bind namespaces
rdf_graph.bind("otn", OTN)
rdf_graph.bind("geo", GEO)
rdf_graph.bind("ext", EXT)

# Function to create a WKT Point
def create_wkt_point(node_id, data):
    lat = data['y']
    lon = data['x']
    return f"POINT({lon} {lat})"


def create_geometry_from_edge_data(edge_data, source_node, target_node):
    if 'geometry' in edge_data:  # Check if geometry data is present
        linestring = edge_data['geometry']
        start_index = linestring.find('(') + 1
        end_index = linestring.find(')')
        if start_index > 0 and end_index > 0:
            coords_string = linestring[start_index:end_index]
            coords_pairs = coords_string.split(', ')
            coords = [(float(lon), float(lat)) for lon, lat in (pair.split(' ') for pair in coords_pairs)]
            return LineString(coords).wkt
    else:
        # Check if source and target nodes have valid coordinates
        if 'x' in graph.nodes[source_node] and 'y' in graph.nodes[source_node] and \
                'x' in graph.nodes[target_node] and 'y' in graph.nodes[target_node]:
            source_coords = (float(graph.nodes[source_node]['x']), float(graph.nodes[source_node]['y']))
            target_coords = (float(graph.nodes[target_node]['x']), float(graph.nodes[target_node]['y']))
            return LineString([source_coords, target_coords]).wkt
    return None

# Process nodes
for node_id, data in graph.nodes(data=True):
    node_uri = URIRef(EXT['Node/' + node_id])
    rdf_graph.add((node_uri, RDF.type, OTN.Node))
    rdf_graph.add((node_uri, RDF.type, EXT.Node))
    rdf_graph.add((EXT.Node, RDFS.subClassOf, OTN.Node))
    # Create a Geometry for the node
    geom_uri = URIRef(GEO['Geometry/' + node_id])
    rdf_graph.add((geom_uri, RDF.type, SF.Point))
    rdf_graph.add((SF.Point, RDFS.subClassOf, GEO.Geometry))
    # Add the WKT literal to the Geometry
    wkt_literal = Literal(create_wkt_point(node_id, data), datatype=GEO.wktLiteral)
    rdf_graph.add((geom_uri, GEO.asWKT, wkt_literal))
    # Link the node to the Geometry
    rdf_graph.add((node_uri, GEO.hasGeometry, geom_uri))

#Generate a road element Id starting from the osmid in data

# Function to generate road element ID
def generate_road_element_id(edge, counter_dict):
    # Extract the OSM IDs from the edge attributes
    osm_ids = edge[2].get('osmid', [])

    # Ensure osm_ids is a list of integers
    if isinstance(osm_ids, str):
        # Assuming osm_ids are separated by commas in the string
        osm_ids = osm_ids.split(',')

    # Convert each ID to string and join with underscore
    base_id = '_'.join(str(osm_id) for osm_id in osm_ids)
    base_id = base_id.replace(" ", "")
    base_id = base_id.replace("[", "")
    base_id = base_id.replace("]", "")

    # Increment the count and append it to the base_id
    counter_dict[base_id] = counter_dict.get(base_id, 0) + 1
    return f"{base_id}_{counter_dict[base_id]}"

def generate_road_id(edge):
    # Extract the OSM IDs from the edge attributes
    osm_ids = edge[2].get('osmid', [])

    # Ensure osm_ids is a list of integers
    if isinstance(osm_ids, str):
        # Assuming osm_ids are separated by commas in the string
        osm_ids = osm_ids.split(',')

    # Convert each ID to string and join with underscore
    base_id = '_'.join(str(osm_id) for osm_id in osm_ids)
    base_id = base_id.replace(" ", "")
    base_id = base_id.replace("[", "")
    base_id = base_id.replace("]", "")

    return f"{base_id}"

counter_dict = {}
# Process edges
for source, target, data in graph.edges(data=True):
    edge = (source, target, data)
    road_element_id = generate_road_element_id(edge, counter_dict)
    road_id = generate_road_id(edge)
    geometry = create_geometry_from_edge_data(data, source, target)
    print(geometry)

    road_id_uri = URIRef(OTN['Road/'] + f"{road_id}")
    road_element_id_uri = URIRef(OTN['Road_Element/'] + f"{road_element_id}")

    # Create a Geometry for the Road element
    geom_uri = URIRef(GEO['Geometry/' + road_element_id])
    rdf_graph.add((geom_uri, RDF.type, SF.LineString))
    rdf_graph.add((SF.LineString, RDFS.subClassOf, GEO.Geometry))
    # Add the WKT literal to the Geometry
    wkt_literal = Literal(create_geometry_from_edge_data(data, source, target), datatype=GEO.wktLiteral)
    rdf_graph.add((geom_uri, GEO.asWKT, wkt_literal))
    # Link the node to the Geometry
    rdf_graph.add((road_element_id_uri, GEO.hasGeometry, geom_uri))

    rdf_graph.add((road_id_uri, RDF.type, OTN.Road))
    rdf_graph.add((road_element_id_uri, RDF.type, OTN.Road_Element))
    rdf_graph.add((road_id_uri, OTN.contains, road_element_id_uri))
    rdf_graph.add((road_element_id_uri, OTN.starts_at, URIRef(EXT['Node/'] + source)))
    rdf_graph.add((road_element_id_uri, OTN.ends_at, URIRef(EXT['Node/'] + target)))


# Serialize the graph in Turtle format
rdf_graph.serialize(destination="output6.ttl", format="turtle")