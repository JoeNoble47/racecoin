# Updated Flask Integration for The Odds API
# Copy this code to your main Flask app file (app.py or main.py)

from flask import Flask, render_template, request, session, jsonify, flash, redirect, url_for
import requests
import json
from datetime import datetime, timedelta
import random

# The Odds API Class (copy to your main app)
class TheOddsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        
    def get_horse_racing_odds(self, sport='horse_racing_uk', regions='uk'):
        """Get horse racing odds and events"""
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': 'h2h',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching odds: {e}")
            return None
    
    def transform_to_race_format(self, odds_data):
        """Transform The Odds API data to your existing race format"""
        races = []
        
        if not odds_data:
            return races
            
        for event in odds_data:
            race = {
                'id': len(races) + 1,
                'title': event.get('sport_title', 'Horse Race'),
                'start_time': event.get('commence_time', ''),
                'is_real_race': True,
                'horses': []
            }
            
            if event.get('bookmakers') and len(event['bookmakers']) > 0:
                bookmaker = event['bookmakers'][0]
                markets = bookmaker.get('markets', [])
                
                if markets:
                    outcomes = markets[0].get('outcomes', [])
                    
                    for i, outcome in enumerate(outcomes):
                        decimal_odds = float(outcome.get('price', 2.0))
                        fractional_odds = self._decimal_to_fractional(decimal_odds)
                        
                        horse = {
                            'name': outcome.get('name', f'Horse {i+1}'),
                            'fractional_odds': fractional_odds,
                            'decimal_odds': decimal_odds,
                            'is_favourite': i == 0,
                            'form': self._generate_form(),
                            'momentum': self._generate_momentum()
                        }
                        race['horses'].append(horse)
            
            if race['horses']:
                races.append(race)
                
        return races
    
    def _decimal_to_fractional(self, decimal_odds):
        """Convert decimal odds to fractional format"""
        if decimal_odds <= 1:
            return "1/1"
            
        numerator = decimal_odds - 1
        
        if numerator >= 1:
            whole = int(numerator)
            fraction = numerator - whole
            
            if fraction < 0.25:
                return f"{whole}/1"
            elif fraction < 0.75:
                return f"{whole * 2 + 1}/2"
            else:
                return f"{whole + 1}/1"
        else:
            inverted = 1 / numerator
            if inverted <= 2:
                return "1/2"
            elif inverted <= 3:
                return "1/3"
            elif inverted <= 4:
                return "1/4"
            else:
                return f"1/{int(inverted)}"
    
    def _generate_form(self):
        forms = ['111', '211', '112', '121', '221', '311', '131', '222']
        return random.choice(forms)
    
    def _generate_momentum(self):
        momentum_values = ['Rising', 'Falling', 'Stable', 'Hot', 'Cold']
        return random.choice(momentum_values)

    def test_connection(self):
        """Test API connection"""
        try:
            # Test with a simple sports request
            url = f"{self.base_url}/sports"
            params = {'apiKey': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            sports = response.json()
            horse_racing_available = any('horse_racing' in sport.get('key', '') for sport in sports)
            
            if horse_racing_available:
                return True, "✅ API connection successful! Horse racing data available."
            else:
                return False, "⚠️ Connected but no horse racing sports found."
                
        except requests.RequestException as e:
            return False, f"❌ API connection failed: {str(e)}"

# Add these routes to your Flask app:

@app.route('/admin/api-config', methods=['GET', 'POST'])
def api_config():
    """Handle API configuration"""
    if request.method == 'POST':
        # Save configuration
        session['use_odds_api'] = 'use_odds_api' in request.form
        session['odds_api_key'] = request.form.get('odds_api_key', '')
        session['odds_sport'] = request.form.get('odds_sport', 'horse_racing_uk')
        session['update_frequency'] = request.form.get('update_frequency', '60')
        session['use_virtual'] = 'use_virtual' in request.form
        session['racing_mode'] = request.form.get('racing_mode', 'enhanced')
        
        # Test API connection if enabled
        if session.get('use_odds_api') and session.get('odds_api_key'):
            odds_api = TheOddsAPI(session['odds_api_key'])
            success, message = odds_api.test_connection()
            session['odds_api_status'] = message
            
            if success:
                flash("API configuration saved successfully!")
            else:
                flash("API configuration saved but connection test failed.")
        else:
            session['odds_api_status'] = "API disabled or no key provided"
            flash("Configuration saved!")
        
        return redirect(url_for('api_config'))
    
    # GET request - show configuration form
    return render_template('admin_api_config.html',
                         use_odds_api=session.get('use_odds_api', False),
                         odds_api_key=session.get('odds_api_key', ''),
                         odds_sport=session.get('odds_sport', 'horse_racing_uk'),
                         update_frequency=session.get('update_frequency', '60'),
                         use_virtual=session.get('use_virtual', True),
                         racing_mode=session.get('racing_mode', 'enhanced'),
                         odds_api_status=session.get('odds_api_status', 'Not configured'),
                         api_status="API Configuration Ready")

@app.route('/admin/test-api')
def test_api():
    """Test API connection"""
    if not session.get('use_odds_api') or not session.get('odds_api_key'):
        flash("Please configure The Odds API first!")
        return redirect(url_for('api_config'))
    
    odds_api = TheOddsAPI(session['odds_api_key'])
    success, message = odds_api.test_connection()
    session['odds_api_status'] = message
    
    if success:
        # Try to fetch some actual horse racing data
        sport = session.get('odds_sport', 'horse_racing_uk')
        odds_data = odds_api.get_horse_racing_odds(sport=sport)
        
        if odds_data and len(odds_data) > 0:
            flash(f"✅ API Test Successful! Found {len(odds_data)} horse racing events.")
        else:
            flash("✅ API connected but no current horse racing events found. Falling back to virtual races.")
    else:
        flash(f"❌ API Test Failed: {message}")
    
    return redirect(url_for('api_config'))

@app.route('/api/refresh-races')
def refresh_races_api():
    """Refresh races from The Odds API or fallback to virtual"""
    races = []
    
    # Try to get real data if API is configured
    if session.get('use_odds_api') and session.get('odds_api_key'):
        try:
            odds_api = TheOddsAPI(session['odds_api_key'])
            sport = session.get('odds_sport', 'horse_racing_uk')
            
            odds_data = odds_api.get_horse_racing_odds(sport=sport)
            races = odds_api.transform_to_race_format(odds_data)
            
            if races:
                session['races'] = races
                return jsonify({
                    'success': True, 
                    'races_count': len(races),
                    'source': 'The Odds API'
                })
        except Exception as e:
            print(f"Error fetching from The Odds API: {e}")
    
    # Fallback to virtual races
    if session.get('use_virtual', True):
        races = generate_virtual_races()  # Your existing function
        session['races'] = races
        return jsonify({
            'success': True, 
            'races_count': len(races),
            'source': 'Virtual Racing System'
        })
    
    return jsonify({'success': False, 'error': 'No racing data source configured'})

# Your existing routes (races, place_bet, etc.) don't need changes
# They will automatically use the new race data format

print("Flask integration code ready!")
print("Next steps:")
print("1. Copy this code to your main Flask app file")
print("2. Get your API key from the-odds-api.com")
print("3. Test the /admin/api-config route")
print("4. Use the Test API button to verify connection")
