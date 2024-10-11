import os
import json
from sqlalchemy import create_engine

# Connect to the database
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
connection = engine.connect()

# Define data folder path
DATA_DIR = "/app/data"

# Loop through data files and parse
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        with open(os.path.join(DATA_DIR, filename), 'r') as file:
            data = json.load(file)
            # Example: Insert parsed data into the table
            for event in data.get("events", []):
                connection.execute(
                    """
                    INSERT INTO events (event_name, start_time, end_time, location)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (event['name'], event['start_time'], event['end_time'], event['location'])
                )

print("Data parsing complete!")