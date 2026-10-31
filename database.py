"""MongoDB persistence for CampusPath graph data."""
import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
from core.graph import CampusGraph, CampusNode, CampusEdge

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DB_NAME', 'campus_navigation')

if not MONGO_URI:
    raise RuntimeError('MONGO_URI is missing. Add it to campus_navigation_agent/.env')

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
_client.admin.command('ping')
_db = _client[DB_NAME]
nodes_collection = _db['campus_nodes']
edges_collection = _db['campus_edges']
nodes_collection.create_index([('id', ASCENDING)], unique=True)
edges_collection.create_index([('source', ASCENDING), ('target', ASCENDING)], unique=True)


def load_campus_graph():
    """Load nodes and edges from MongoDB into the existing graph classes."""
    node_docs = list(nodes_collection.find({}, {'_id': 0}))
    edge_docs = list(edges_collection.find({}, {'_id': 0}))
    if not node_docs or not edge_docs:
        raise RuntimeError(
            'MongoDB is connected, but campus collections are empty. '
            'Run: python seed_mongodb.py'
        )

    graph = CampusGraph()
    for doc in node_docs:
        graph.add_node(CampusNode(**doc))

    for doc in edge_docs:
        doc.pop('travel_time', None)
        graph.add_edge(CampusEdge(**doc))
    return graph


def save_graph(graph):
    """Persist current node and pathway state without replacing the collections."""
    for node in graph.nodes.values():
        nodes_collection.update_one(
            {'id': node.id}, {'$set': node.to_dict()}, upsert=True
        )

    # Store one canonical document per undirected pathway.
    seen = set()
    for edge_list in graph.edges.values():
        for edge in edge_list:
            key = tuple(sorted((edge.source, edge.target)))
            if key in seen:
                continue
            seen.add(key)
            doc = edge.to_dict()
            doc.pop('travel_time', None)
            edges_collection.update_one(
                {'source': key[0], 'target': key[1]},
                {'$set': {**doc, 'source': key[0], 'target': key[1]}},
                upsert=True
            )


def get_database_status():
    return {
        'database': DB_NAME,
        'connected': True,
        'nodes': nodes_collection.count_documents({}),
        'edges': edges_collection.count_documents({})
    }
