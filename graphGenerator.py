import osmnx as ox
from shapely.geometry import Polygon

cords= ((12.3047, 45.4455), (12.2995, 45.4389), (12.3052, 45.4368), (12.3084, 45.4411), (12.3140, 45.4418), (12.3061, 45.4463), (12.3047, 45.4455))
polygon= Polygon(cords)
G=ox.graph_from_polygon(polygon, network_type='all', retain_all=True, simplify=True)
#U = G.to_undirected()
#ox.save_graph_geopackage(U, filepath="./graph1.gpkg")
ox.save_graphml(G, filepath="./graph.graphml")
print(G.edges.data())
