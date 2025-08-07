from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, render_template_string
import os
import random
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-12345')

# Simple user storage
users = {
    'demo': {'password': 'password', 'racecoins': 1000, 'bet_history': []},
    'admin': {'password': 'admin123', 'racecoins': 10000, 'bet_history': []}
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return f"<h1>Welcome {session['username']}!</h1><p>Racecoins: {users[session['username']]['racecoins']}</p><a href='/logout'>Logout</a>"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'users': list(users.keys())})

@app.route('/debug/users')
def debug_users():
    return jsonify({
        'users': list(users.keys()),
        'details': {k: {'password': v['password'], 'racecoins': v['racecoins']} for k, v in users.items()}
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"LOGIN ATTEMPT: username='{username}', password='{password}'")
        print(f"AVAILABLE USERS: {list(users.keys())}")
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            print(f"LOGIN SUCCESS for {username}")
            return redirect(url_for('index'))
        else:
            print(f"LOGIN FAILED: username={username}, password={password}")
            error = f"Invalid credentials. Try: demo/password or admin/admin123"
            return render_template_string(LOGIN_HTML, error=error)
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Simple HTML templates as strings (no external files needed)
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head><title>RaceCoin Login</title></head>
<body>
    <h1>RaceCoin Login</h1>
    {% if error %}
        <p style="color:red;">{{ error }}</p>
    {% endif %}
    <form method="post">
        <p>Username: <input type="text" name="username" required></p>
        <p>Password: <input type="password" name="password" required></p>
        <p><button type="submit">Login</button></p>
    </form>
    <hr>
    <h3>Test Accounts:</h3>
    <p><strong>Demo:</strong> username=demo, password=password</p>
    <p><strong>Admin:</strong> username=admin, password=admin123</p>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
