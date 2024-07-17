from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS
from utils import is_point_covered, process_transcript
import sqlite3

# import mysql.connector
# mydb = mysql.connector.connect(
#     host = "localhost",
#     user = "root",
#     password = "Teamb1#123",
#     database = "neurocator",
#     auth_plugin='mysql_native_password'
# )
# cursor = mydb.cursor()

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
cur.execute("INSERT INTO neurocator (name) VALUES (hi)")  # Limiting to 10 rows for safety

app = Flask(__name__)
CORS(app)

# Initialize the SQLite database for the to-do list
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (task TEXT, completed BOOLEAN)''')
        conn.commit()

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        return render_template('login.html.j2')

# @app.route('/')
# def index():
#     return render_template('index.html.j2')

@app.route('/live', methods=['GET', 'POST'])
def live():
    if request.method == 'POST':
        points = request.form.getlist('points')
        points = [{"text": point, "covered": False} for point in points]
        return render_template('live.html.j2', points=points)
    return render_template('live.html.j2', points=[])

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        transcript = data.get('transcript', '')
        points = data.get('points', [])
        
        if not transcript or not points:
            return jsonify({"error": "Invalid input data"}), 400

        transcript_tokens = process_transcript(transcript)
        print(f"Transcript Tokens: {transcript_tokens}")

        for point in points:
            if is_point_covered(transcript_tokens, point['text']):
                point['covered'] = True
                print(f"Point '{point['text']}' covered")
            else:
                point['covered'] = False
                print(f"Point '{point['text']}' not covered")

        return jsonify(points)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    return render_template('forum.html.j2')

@app.route('/longtermplanning')
def planning():
    return render_template('longtermplanning.html.j2')

@app.route('/resources')
def resources():
    return render_template('resources.html.j2')

@app.route('/about')
def about():
    return render_template('about_us.html.j2')

# To-Do List routes
@app.route('/todo', methods=['GET', 'POST'])
def to_do_list():
    if request.method == 'POST':
        task = request.form['task']
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO tasks (task, completed) VALUES (?, ?)', (task, False))
            conn.commit()
        return redirect(url_for('to_do_list'))
    
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT rowid, task, completed FROM tasks')
        tasks = [(rowid, task, completed) for rowid, task, completed in c.fetchall()]
    
    print(f"Tasks: {tasks}")  # Debug output
    return render_template('to_do_list.html.j2', tasks=tasks)

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    try:
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT completed FROM tasks WHERE rowid = ?', (task_id,))
            completed = c.fetchone()[0]
            c.execute('UPDATE tasks SET completed = ? WHERE rowid = ?', (not completed, task_id))
            conn.commit()
        return redirect(url_for('to_do_list'))
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/faq')
def faq():
    return render_template('faq.html.j2')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)