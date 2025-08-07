from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
import random
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Configuration
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# In-memory storage for demo purposes (in production, use a proper database)
users = {
    'demo': {
        'password': 'password',
        'racecoins': 1000,
        'bet_history': []
    },
    'admin': {
        'password': 'admin123',
        'racecoins': 10000,
        'bet_history': []
    }
}

races_data = []
api_config = {
    'enabled': False,
    'api_type': 'sample_data',
    'api_key': '',
    'region': 'uk'
}

# Sample horse names for race generation
horse_names = [
    'Thunder Bolt', 'Lightning Strike', 'Storm Chaser', 'Wind Runner', 'Fire Flash',
    'Silver Arrow', 'Golden Gallop', 'Midnight Express', 'Racing Spirit', 'Victory Lane',
    'Swift Shadow', 'Blazing Star', 'Diamond Dust', 'Royal Thunder', 'Crimson Comet'
]

def generate_race_data():
    """Generate sample race data for demonstration"""
    race_time = datetime.now() + timedelta(minutes=random.randint(5, 30))
    horses = random.sample(horse_names, random.randint(6, 12))
    
    race = {
        'id': len(races_data) + 1,
        'name': f'Race {len(races_data) + 1}',
        'time': race_time.strftime('%Y-%m-%d %H:%M'),
        'track': random.choice(['Ascot', 'Cheltenham', 'Epsom', 'Newmarket', 'York']),
        'horses': []
    }
    
    for i, horse in enumerate(horses, 1):
        odds = random.uniform(2.0, 15.0)
        race['horses'].append({
            'number': i,
            'name': horse,
            'odds': round(odds, 1),
            'jockey': f'Jockey {i}'
        })
    
    return race

@app.route('/health')
def health_check():
    """Simple health check for deployment"""
    return jsonify({'status': 'healthy', 'users_available': list(users.keys())})

@app.route('/debug/users')
def debug_users():
    """Debug route to check available users"""
    return jsonify({
        'users': list(users.keys()),
        'user_details': {k: {'password': v['password'], 'racecoins': v['racecoins']} for k, v in users.items()}
    })

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Generate some sample races if none exist
    if not races_data:
        for _ in range(5):
            races_data.append(generate_race_data())
    
    return render_template('races.html', races=races_data[:3], user_coins=users[session['username']]['racecoins'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Debug logging
        print(f"Login attempt - Username: '{username}', Password: '{password}'")
        print(f"Available users: {list(users.keys())}")
        if username in users:
            print(f"User found. Expected password: '{users[username]['password']}'")
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            flash('Username already exists', 'error')
        else:
            users[username] = {
                'password': password,
                'racecoins': 1000,  # Starting balance
                'bet_history': []
            }
            session['username'] = username
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/debug/users')
def debug_users():
    """Debug route to check available users"""
    return jsonify({
        'users': list(users.keys()),
        'user_details': {k: {'password': v['password'], 'racecoins': v['racecoins']} for k, v in users.items()}
    })

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/races')
def races():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Generate more races if needed
    while len(races_data) < 10:
        races_data.append(generate_race_data())
    
    return render_template('races.html', races=races_data, user_coins=users[session['username']]['racecoins'])

@app.route('/place_bet/<int:race_id>')
def place_bet(race_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    race = next((r for r in races_data if r['id'] == race_id), None)
    if not race:
        flash('Race not found', 'error')
        return redirect(url_for('races'))
    
    return render_template('place_bet.html', race=race, user_coins=users[session['username']]['racecoins'])

@app.route('/submit_bet', methods=['POST'])
def submit_bet():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    race_id = int(request.form['race_id'])
    horse_number = int(request.form['horse_number'])
    bet_amount = float(request.form['bet_amount'])
    bet_type = request.form.get('bet_type', 'win')
    
    user = users[session['username']]
    
    if bet_amount > user['racecoins']:
        flash('Insufficient Racecoins', 'error')
        return redirect(url_for('place_bet', race_id=race_id))
    
    # Deduct bet amount
    user['racecoins'] -= bet_amount
    
    # Store bet
    bet = {
        'race_id': race_id,
        'horse_number': horse_number,
        'amount': bet_amount,
        'type': bet_type,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    user['bet_history'].append(bet)
    
    flash(f'Bet placed successfully! {bet_amount} Racecoins on horse {horse_number}', 'success')
    return redirect(url_for('races'))

@app.route('/multi_bet')
def multi_bet():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('multi_bet.html', races=races_data[:5], user_coins=users[session['username']]['racecoins'])

@app.route('/race_animation/<int:race_id>')
def race_animation(race_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    race = next((r for r in races_data if r['id'] == race_id), None)
    if not race:
        flash('Race not found', 'error')
        return redirect(url_for('races'))
    
    return render_template('race_animation.html', race=race)

@app.route('/multi_race_animation')
def multi_race_animation():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('multi_race_animation.html', races=races_data[:3])

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Generate sample results
    sample_results = []
    for race in races_data[:5]:
        winner = random.choice(race['horses'])
        sample_results.append({
            'race': race,
            'winner': winner,
            'time': race['time']
        })
    
    return render_template('results.html', results=sample_results)

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = users[session['username']]
    return render_template('profile.html', user=user, username=session['username'])

@app.route('/leaderboard')
def leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Create leaderboard from users
    leaderboard_data = []
    for username, user_data in users.items():
        leaderboard_data.append({
            'username': username,
            'racecoins': user_data['racecoins'],
            'total_bets': len(user_data['bet_history'])
        })
    
    leaderboard_data.sort(key=lambda x: x['racecoins'], reverse=True)
    
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/admin/api-config')
def admin_api_config():
    if 'username' not in session or session['username'] != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    return render_template('admin_api_config.html', config=api_config)

@app.route('/admin/update-api-config', methods=['POST'])
def update_api_config():
    if 'username' not in session or session['username'] != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    api_config['enabled'] = 'api_enabled' in request.form
    api_config['api_type'] = request.form.get('api_type', 'free_racing_data')
    api_config['api_key'] = request.form.get('api_key', '')
    api_config['region'] = request.form.get('region', 'uk')
    
    flash('API configuration updated successfully', 'success')
    return redirect(url_for('admin_api_config'))

# API endpoints for AJAX calls
@app.route('/api/race-status/<int:race_id>')
def race_status(race_id):
    race = next((r for r in races_data if r['id'] == race_id), None)
    if race:
        return jsonify({'status': 'upcoming', 'time': race['time']})
    return jsonify({'status': 'not_found'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
