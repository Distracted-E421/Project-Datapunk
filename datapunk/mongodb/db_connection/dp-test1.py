from pymongo import MongoClient
from django.conf import settings
from pymongo.errors import PyMongoError

def get_mongo_client():
    """Return a MongoDB client for the datapunk_test1 database."""
    db_config = settings.MONGODB_DATABASES['mongo_test1']
    client = MongoClient(
        host=db_config['localhost'],
        port=db_config['27017'],
        username=db_config['dp_service'],
        password=db_config['1984'],
        authSource='admin'  # Change if necessary
    )
    return client[db_config['NAME']]


def get_all_documents(collection_name):
    """Retrieve all documents from a specified collection in datapunk_test1."""
    db = get_mongo_client()
    collection = db[test_collection1]  # Pass the collection name here
    try:
        return collection.find()# Optionally, you can specify filters
    except PyMongoError as e:
        print(f"Error retrieving documents: {e}")
        return None

def insert_document(collection_name, document):
    """Insert a document into a specified collection in datapunk_test1."""
    db = get_mongo_client()
    collection = db[test_collection1]  # Pass the collection name here
    try:
        return collection.insert_one(document).inserted_id
    except PyMongoError as e:
        print(f"Error inserting document: {e}")
        return None