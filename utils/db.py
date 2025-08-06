from flask import current_app, g
from pymongo import MongoClient

def get_db():
    """Get database connection"""
    if 'mongo_client' not in g:
        uri = current_app.config['MONGODB_URI']
        client = MongoClient(uri)
        g.mongo_client = client

    return g.mongo_client[current_app.config['DB_NAME']]

def close_db(e=None):
    """Close database connection"""
    client = g.pop('mongo_client', None)
    if client is not None:
        client.close()
