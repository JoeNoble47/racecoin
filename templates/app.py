from flask import Flask, request, jsonify
import os

app = Flask(__name__)
app.secret_key = 'test-key'

users = {
    'demo': {'password': 'password', 'racecoins': 1000},
    'admin': {'password': 'admin123', 'racecoins': 10000}
}

@app.route('/')
def home():
    return '''
    <h1>RaceCoin Test App</h1>
    <p><a href="/health">Health Check</a></p>
    <p><a href="/debug/users">Debug Users</a></p>
    <p><a href="/test-login">Test Login</a></p>
    '''

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'users': list(users.keys())})

@app.route('/debug/users')
def debug_users():
    return jsonify({
        'users': list(users.keys()),
        'details': {k: {'password': v['password'], 'racecoins': v['racecoins']} for k, v in users.items()}
    })

@app.route('/test-login')
def test_login():
    return '''
    <h1>Test Login</h1>
    <form method="post" action="/do-login">
        <p>Username: <input type="text" name="username" value="admin"></p>
        <p>Password: <input type="password" name="password" value="admin123"></p>
        <p><button type="submit">Test Login</button></p>
    </form>
    '''

@app.route('/do-login', methods=['POST'])
def do_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    print(f"LOGIN TEST: username='{username}', password='{password}'")
    
    if username in users and users[username]['password'] == password:
        return f"<h1>SUCCESS!</h1><p>Login worked for {username}</p>"
    else:
        return f"<h1>FAILED</h1><p>Login failed for username='{username}', password='{password}'</p><p>Available: {list(users.keys())}</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
