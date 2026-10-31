"""One-time import of this project's current graph into MongoDB.

This script will NOT delete or overwrite existing MongoDB records.
"""
from core.graph import create_default_campus_graph
from database import nodes_collection, edges_collection

if nodes_collection.count_documents({}) or edges_collection.count_documents({}):
    raise SystemExit(
        'Import stopped: MongoDB already contains campus data. '
        'No records were changed. Back up and review the collections before importing.'
    )

graph = create_default_campus_graph()
node_docs = [node.to_dict() for node in graph.nodes.values()]
edge_docs = []
seen = set()
for edge_list in graph.edges.values():
    for edge in edge_list:
        key = tuple(sorted((edge.source, edge.target)))
        if key in seen:
            continue
        seen.add(key)
        doc = edge.to_dict()
        doc.pop('travel_time', None)
        doc['source'], doc['target'] = key
        edge_docs.append(doc)

nodes_collection.insert_many(node_docs)
if edge_docs:
    edges_collection.insert_many(edge_docs)

print(f'Imported {len(node_docs)} campus nodes and {len(edge_docs)} pathways into MongoDB.')
print('This is the existing project graph. Verify its campus data separately before real-world use.')
