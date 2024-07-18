import os
import psycopg2
from jinja2 import Environment, FileSystemLoader

# Database connection parameters
db_params = {
    'dbname': 'neurocator',
    'user': 'neurocator_owner',
    'password': 'cLDe5qNvzUO1',  # In production, use environment variables for sensitive data
    'host': 'ep-dark-forest-a6dtlznj.us-west-2.aws.neon.tech',
    'port': '5432'  # Default PostgreSQL port, change if your setup is different
}

# Connect to the database
conn = psycopg2.connect(**db_params)

# Create a cursor
cur = conn.cursor()

# Execute a query (replace with your actual query)
cur.execute("INSERT INTO neurocator (name) VALUES ('hi')")  # Limiting to 10 rows for safety

conn.commit()