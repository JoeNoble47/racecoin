from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>BASIC TEST - Version 3</h1><p>If you see this, Flask is working!</p>'

@app.route('/test')
def test():
    return '<h1>TEST ROUTE WORKS</h1>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
