import os
import psycopg2
from jinja2 import Environment, FileSystemLoader

# Database connection parameters
db_params = {
    'dbname': 'neurocator',
    'user': 'neurocator_owner',
    'password': '3j1HgiIuwVoO',  # In production, use environment variables for sensitive data
    'host': 'ep-autumn-scene-a6huvqfz.us-west-2.aws.neon.tech',
    'port': '5432'  # Default PostgreSQL port, change if your setup is different
}

print("hello")

# Connect to the database
conn = psycopg2.connect(**db_params)

# Create a cursor
cur = conn.cursor()

# Execute a query (replace with your actual query)
#cur.execute("SELECT password FROM users")  # Limiting to 10 rows for safety
#query = "SELECT username FROM users WHERE password=%s"
#queryVars = ("123",)
#cur.execute(query, queryVars)
#results = cur.fetchall()

query = "INSERT INTO test (name) VALUES (test)"
cur.execute(query)
conn.commit()
