import os
import psycopg2
import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection parameters
db_params = {
    'dbname': os.getenv('PGDATABASE', 'neurocator'),
    'user': os.getenv('PGUSER', 'neurocator_owner'),
    'password': os.getenv('PGPASSWORD', '3j1HgiIuwVoO'),
    'host': os.getenv('PGHOST', 'ep-autumn-scene-a6huvqfz.us-west-2.aws.neon.tech'),
    'port': os.getenv('PGPORT', '5432'),
    'sslmode': 'require'
}

def get_db_connection():
    conn = psycopg2.connect(**db_params)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            task TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

session_username_key = 'neurocator_username'
app.config['SECRET_KEY'] = "bflerjvnlkrv#123"

# Initialize the database
@app.before_first_request
def initialize():
    init_db()

# Utility functions
def is_point_covered(transcript_tokens, point_text):
    return point_text.lower() in transcript_tokens

def process_transcript(transcript):
    return transcript.split()

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':    
        return render_template('login.html.j2', username=session.get(session_username_key))

@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if request.method == 'GET':
        return render_template('signup.html.j2')
    else:
        inputEmail = request.values.get("email")
        inputUsername = request.values.get("username")
        userTypedPassword = request.values.get("password")
        securedPassword = generate_password_hash(userTypedPassword)
        query = "SELECT username FROM users WHERE username=%s"
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (inputUsername,))
        results = cur.fetchall()
        if len(results) == 1:
            conn.close()
            return redirect(url_for('signUp', usernameTaken=True))
        else:
            query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
            cur.execute(query, (inputEmail, inputUsername, securedPassword))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

@app.route('/checklogin', methods=['POST'])
def checkLogin():
    inputUsername = request.values.get("username")
    inputPassword = request.values.get("password")
    query = "SELECT password FROM users WHERE username=%s"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, (inputUsername,))
    results = cur.fetchall()
    if len(results) == 1:
        hashedPassword = results[0][0]
        conn.close()
        if check_password_hash(hashedPassword, inputPassword):
            session[session_username_key] = inputUsername
            return redirect(url_for('home'))
        else:
            return redirect(url_for('index', incorrectLoginError=True))
    else:
        conn.close()
        return redirect(url_for('index', incorrectLoginError=True))

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html.j2')

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    conn = get_db_connection()
    cur = conn.cursor()
    query = "SELECT id, username, title, content, date FROM posts"
    cur.execute(query)
    rows = cur.fetchall()
    posts = []
    for row in reversed(rows):
        post = {
            'id': row[0], 
            'username': row[1],
            'title': row[2],
            'content': row[3],
            'date': row[4]
        }
        posts.append(post)
    conn.close()
    return render_template('forum.html.j2', posts=posts)

@app.route('/addpost', methods=['GET', 'POST'])
def addPost():
    if session.get(session_username_key) is None:
        return redirect(url_for('index'))
    if request.method == 'GET':
        username = session.get(session_username_key)
        return render_template('addpost.html.j2', username=username)
    else:
        username = session.get(session_username_key)
        inputTitle = request.values.get("title")
        inputContent = request.values.get("content")
        conn = get_db_connection()
        cur = conn.cursor()
        query = "INSERT INTO posts (username, title, content) VALUES (%s, %s, %s)"
        cur.execute(query, (username, inputTitle, inputContent))
        conn.commit()
        conn.close()
        return redirect(url_for('forum'))
    

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
            if not point['covered'] and is_point_covered(transcript_tokens, point['text']):
                point['covered'] = True
                print(f"Point '{point['text']}' covered")

            for subpoint in point.get('subpoints', []):
                if not subpoint['covered'] and is_point_covered(transcript_tokens, subpoint['text']]):
                    subpoint['covered'] = True
                    print(f"Subpoint '{subpoint['text']}' covered")

        return jsonify(points)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/longtermplanning')
def planning():
    return render_template('longtermplanning.html.j2')

@app.route('/resources')
def resources():
    return render_template('resources.html.j2')

@app.route('/about')
def about():
    return render_template('about_us.html.j2')

@app.route('/todo', methods=['GET', 'POST'])
def to_do_list():
    if request.method == 'POST':
        task = request.form['task']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO tasks (task, completed) VALUES (%s, %s)', (task, False))
        conn.commit()
        conn.close()
        return redirect(url_for('to_do_list'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, task, completed FROM tasks')
    tasks = [(id, task, completed) for id, task, completed in cur.fetchall()]
    conn.close()
    
    return render_template('to_do_list.html.j2', tasks=tasks)

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('to_do_list'))
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/faq')
def faq():
    return render_template('faq.html.j2')

@app.route('/download/<path:filename>')
def download(filename):
    directory = os.path.join(app.root_path, 'static/files/article')
    return send_from_directory(directory, filename)

# general server-side validation 
def serverSideValidation(inputs):
    validated = True
    for input in inputs:
        if len(request.values.get(input)) == 0:
            validated = False
    return validated

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)