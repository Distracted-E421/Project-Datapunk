from pymongo import MongoClient
from django.conf import settings
from pymongo.errors import PyMongoError

def get_mongo_client(db_key='mongo_test3'):
    """Return a MongoDB client for the specified database."""
    db_config = settings.MONGODB_DATABASES[db_key]
    client = MongoClient(
        host=db_config['HOST'],        
        port=db_config['PORT'],        
        username=db_config['USER'],    
        password=db_config['PASSWORD'],
        authSource='admin'             
    )
    return client[db_config['NAME']]

def get_all_documents(collection_name, db_key='mongo_test3'):
    """Retrieve all documents from a specified collection."""
    db = get_mongo_client(db_key)
    collection = db[collection_name]
    try:
        documents = collection.find()  # Get cursor
        return list(documents)         # Convert cursor to list before returning
    except PyMongoError as e:
        print(f"Error retrieving documents: {e}")
        return None

def insert_document(collection_name, document, db_key='mongo_test3'):
    """Insert a document into a specified collection."""
    db = get_mongo_client(db_key)
    collection = db[collection_name]
    try:
        return collection.insert_one(document).inserted_id
    except PyMongoError as e:
        print(f"Error inserting document: {e}")
        return None