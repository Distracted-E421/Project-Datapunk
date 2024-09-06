from pymongo import MongoClient
from django.conf import settings

# MongoDB Configuration from settings
def get_mongo_client(db_key):
    db_config = settings.MONGODB_DATABASES[db_key]
    client = MongoClient(
        host=db_config['HOST'],
        port=db_config['PORT'],
        username=db_config['USER'],
        password=db_config['PASSWORD'],
        authSource='admin'  # Change this if needed
    )
    return client[db_config['NAME']]

# You can add other MongoDB operations here, like inserting documents, querying, etc.

def get_all_documents(collection_name, db_key='mongo_test1'):
    db = get_mongo_client(db_key)
    collection = db[collection_name]
    documents = collection.find()  # Query all documents in the collection
    return documents

def insert_document(collection_name, document, db_key='mongo_test1'):
    db = get_mongo_client(db_key)
    collection = db[collection_name]
    result = collection.insert_one(document)  # Insert a single document
    return result.inserted_id
