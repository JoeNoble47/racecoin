# RaceCoin - Virtual Horse Racing App
from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
from datetime import datetime, timedelta, date
import time

# Environment configuration
os.environ['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'development')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Branding Configuration
APP_NAME = "RaceCoin"
APP_TAGLINE = "Virtual Horse Racing & Betting"
APP_DESCRIPTION = "The ultimate virtual horse racing experience"
CURRENCY_NAME = "RaceCoins"
CURRENCY_SYMBOL = "RC"
APP_VERSION = "2.0"
APP_AUTHOR = "RaceCoin Gaming"

# Database setup
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            coins INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            total_bets INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Add context processor for branding
@app.context_processor
def inject_branding():
    return {
        'app_name': APP_NAME,
        'app_tagline': APP_TAGLINE,
        'app_description': APP_DESCRIPTION,
        'currency_name': CURRENCY_NAME,
        'currency_symbol': CURRENCY_SYMBOL,
        'app_version': APP_VERSION,
        'app_author': APP_AUTHOR
    }

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('races'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('races'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/races')
@login_required
def races():
    # Generate virtual races compatible with your templates
    horse_names = [
        'Thunder Bolt', 'Lightning Strike', 'Storm Runner', 'Fire Flash', 
        'Wind Walker', 'Golden Arrow', 'Silver Bullet', 'Royal Champion',
        'Midnight Express', 'Golden Thunder', 'Swift Arrow', 'Dancing Star'
    ]
    
    races = []
    for i in range(3):
        race_horses = random.sample(horse_names, 6)
        race = {
            'id': i + 1,
            'meeting_name': f'RaceCoin Track - Race {i + 1}',
            'start_time': (datetime.now() + timedelta(hours=i+1)).isoformat(),
            'track': 'RaceCoin Racecourse',
            'race_number': i + 1,
            'runners': []
        }
        
        for idx, horse in enumerate(race_horses):
            race['runners'].append({
                'name': horse,
                'number': idx + 1,
                'odds': {
                    'decimal': round(random.uniform(2.0, 8.0), 2)
                },
                'jockey': f'Jockey {idx + 1}',
                'weight': f'{random.randint(8, 10)}-{random.randint(0, 13)}'
            })
        
        races.append(race)
    
    return render_template('races.html', races=races)

@app.route('/place_bet/<int:race_id>')
@login_required
def place_bet(race_id):
    return render_template('place_bet.html', race_id=race_id)

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('login'))
    
    user_dict = dict(user)
    # Add required fields that templates expect
    user_dict['xp'] = 0
    user_dict['rank'] = 'Rookie'
    user_dict['number_rank'] = 1
    user_dict['current_streak'] = 0
    user_dict['biggest_single_win'] = 0
    user_dict['login_streak'] = 0
    
    return render_template('profile.html', user=user_dict, achievements=[])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
