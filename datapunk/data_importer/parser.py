import json
import csv

def parse_file(file_path):
    """Parse a file based on its format."""
    if file_path.endswith('.json'):
        return parse_json(file_path)
    elif file_path.endswith('.csv'):
        return parse_csv(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        return None

def parse_json(file_path):
    """Parse a JSON file."""
    try:
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Error parsing JSON file {file_path}: {e}")
        return None

def parse_csv(file_path):
    """Parse a CSV file."""
    try:
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            return [row for row in reader]
    except Exception as e:
        print(f"Error parsing CSV file {file_path}: {e}")
        return None