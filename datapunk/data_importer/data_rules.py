import os
import logging

# Ensure the 'data_logs' directory exists
log_dir = os.path.join(os.path.dirname(__file__), 'data_logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging
logging.basicConfig(filename=os.path.join(log_dir, 'import_log.txt'), level=logging.INFO)

def log_import(file_name, status):
    """Log the result of each file import."""
    logging.info(f"File {file_name} import status: {status}")

def determine_db_and_collection(filename, data):
    """Determine which database and collection to use based on filename or data content."""
    if 'users' in filename:
        return 'mongo_test1', 'users'
    elif 'orders' in filename:
        return 'mongo_prod1', 'orders'
    else:
        return 'mongo_test1', 'default'
