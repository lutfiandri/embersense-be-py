from flask import Flask, jsonify, request
from flask_cors import CORS

from shapely.geometry import Polygon, Point
import math
from shapely.affinity import rotate

app = Flask(__name__)
CORS(app)



# RECOMMENDATION ALGORITHM =========================================================

def get_recommended_length_triangle(polygon, n_nodes):
    A = polygon.area
    N = n_nodes
    
    return math.sqrt((A/N)*(2/math.sqrt(3)))

def get_recommended_length_square(polygon, n_nodes):
    A = polygon.area
    N = n_nodes
    
    constant_factor = 0.99
    
    return math.sqrt(A/N) * constant_factor

def get_nodes_square(polygon, node_length, degree, minx, maxx, miny, maxy):
    # Calculate the number of nodes needed in each direction
    x_nodes = math.ceil((maxx - minx) / node_length)
    y_nodes = math.ceil((maxy - miny) / node_length)
    # Calculate the starting point for the nodes
    start_x = minx + (node_length / 2)
    start_y = miny + (node_length / 2)
    
    # Create a list to store the nodes
    nodes = []
    # Loop through each row and column of nodes
    for i in range(x_nodes):
        for j in range(y_nodes):
            # Calculate the coordinates of the node
            x = start_x + (i * node_length)
            y = start_y + (j * node_length)
            node = Point(x, y)
            # Rotate the node around the centroid of the polygon
            centroid = polygon.centroid
            node = rotate(node, degree, origin=centroid)
            # Check if the node is inside the polygon
            if polygon.contains(node):
                nodes.append(node)
    return nodes


def get_nodes_triangle(polygon, node_length, degree, minx, maxx, miny, maxy):
    # Calculate the side length of the equilateral triangle
    side_length = node_length / math.sqrt(3)

    # Calculate the number of rows and columns of triangles needed
    x_nodes = math.ceil((maxx - minx) / (side_length))
    y_nodes = math.ceil((maxy - miny) / (side_length))

    # Create a list to store the nodes (equilateral triangle vertices)
    nodes = []

    # Loop through each row and column of nodes
    for i in range(x_nodes):
        for j in range(y_nodes):
            # Calculate the coordinates of the center of the equilateral triangle
            x = minx + (node_length * i)
            
            if j % 2 == 0:
                x += node_length/2
            else:
                pass
            y = miny + (math.sqrt(3) * node_length * j / 2)
            
            node = Point(x, y)
            
            centroid = polygon.centroid
            node = rotate(node, degree, origin=centroid)

            # Check if all vertices are within the polygon
            if polygon.contains(node):
                nodes.append(node)

    return nodes

def fill_polygon_with_nodes(polygon, node_length, degree, pattern):
    # Create a bounding box around the polygon
    minx, miny, maxx, maxy = polygon.bounds
    
    # Adust xyxy
    radius = Point(minx, miny).distance(polygon.centroid)
    maxx = polygon.centroid.x + radius
    minx = polygon.centroid.x - radius
    maxy = polygon.centroid.y + radius
    miny = polygon.centroid.y - radius

    nodes = []
    
    if pattern=='triangle':
        nodes = get_nodes_triangle(polygon, node_length, degree, minx, maxx, miny, maxy)
    else:
        nodes = get_nodes_square(polygon, node_length, degree, minx, maxx, miny, maxy)

    return nodes
    

# ROUTING =====================================================================================

@app.route("/")
def index():
    return jsonify({
        'message': 'welcome to embersense-be-py'
    }), 200

@app.route("/recommend-by-distance", methods=["POST"])
def recommend_by_distance():
    try:
        body = request.json

        print(body)

        polygon = Polygon(body['polygon'])
        node_length = body['node_length']
        degree = body['degree']
        pattern = body['pattern']

        if degree == None:
            degree = 0

        if pattern == None:
            pattern = 'triangle'


        nodes = fill_polygon_with_nodes(polygon, node_length, degree, pattern)

        nodes = [[node.x, node.y] for node in nodes]

        return jsonify({
            'nodes': nodes,
            'node_count': len(nodes),
            'node_length': node_length,
            'degree': degree
        })
        
    except Exception as error:
        return jsonify({
            'error': str(error)
        }, 500)
    


@app.route("/recommend-by-count", methods=["POST"])
def recommend_by_count():
    try:
        body = request.json

        print(body)

        polygon = Polygon(body['polygon'])
        count = body['count']
        degree = body['degree']
        pattern = body['pattern']

        if count == None:
            raise Exception("field count is empty")

        if degree == None:
            degree = 0

        if pattern == None:
            pattern = 'triangle'

        node_length = 0
        if pattern == 'triangle':
            node_length = get_recommended_length_triangle(polygon, count)
        else:
            node_length = get_recommended_length_square(polygon, count)

        nodes = fill_polygon_with_nodes(polygon, node_length, degree, pattern)

        nodes = [[node.x, node.y] for node in nodes]

        return jsonify({
            'nodes': nodes,
            'node_count': len(nodes),
            'node_length': node_length,
            'degree': degree
        })
        
    except Exception as error:
        return jsonify({
            'error': str(error)
        }, 500)


if __name__ == "__main__":
    app.run(port=5001)


