import os
from data_importer.parser import parse_file
from data_importer.data_rules import determine_db_and_collection, log_import
from pymongo import MongoClient
from mongodb import dp_test1, dp_test2, dp_test3, dp_prod1, dp_prod2  # MongoDB connection files

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_dump')

# Map db_key to the appropriate MongoDB connection file
DB_CONNECTIONS = {
    'mongo_test1': dp_test1,
    'mongo_test2': dp_test2,
    'mongo_test3': dp_test3,
    'mongo_prod1': dp_prod1,
    'mongo_prod2': dp_prod2,
}

def import_data():
    """Main method to scan the data_dump directory and import data."""
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        print(f"Processing file: {filename}")
        
        try:
            # Parse the file based on its format
            data = parse_file(file_path)
            
            if data:
                # Determine the database and collection based on file content or rules
                db_key, collection_name = determine_db_and_collection(filename, data)
                
                # Insert the data into the appropriate MongoDB collection
                if db_key and collection_name:
                    insert_data_into_db(db_key, collection_name, data)
                    log_import(filename, "Success")
                else:
                    print(f"Failed to determine database or collection for {filename}")
                    log_import(filename, "Failed: Unable to determine database or collection")
            else:
                log_import(filename, "Failed: No data returned from parser")
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            log_import(filename, f"Failed: {e}")

def insert_data_into_db(db_key, collection_name, data):
    """Inserts data into the determined MongoDB database and collection."""
    # Get the MongoDB connection module based on db_key
    db_module = DB_CONNECTIONS.get(db_key)
    
    if not db_module:
        print(f"Invalid database key: {db_key}")
        return
    
    db_client = db_module.get_mongo_client(db_key)
    collection = db_client[collection_name]
    
    try:
        if isinstance(data, list):  # If it's a list of documents
            result = collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents into {collection_name}")
        else:  # Single document
            result = collection.insert_one(data)
            print(f"Inserted document with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting data into {collection_name}: {e}")
