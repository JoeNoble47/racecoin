# The Odds API Integration Example for Virtual Horse Betting
# Replace your existing Betfair API code with this implementation

import requests
import json
from datetime import datetime, timedelta
import random

class TheOddsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        
    def get_horse_racing_odds(self, sport='horse_racing_uk', regions='uk'):
        """
        Get horse racing odds and events
        
        Args:
            sport: 'horse_racing_uk', 'horse_racing_us', or 'horse_racing_au'
            regions: 'uk', 'us', 'au'
        """
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': 'h2h',  # head-to-head betting
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
        """
        Transform The Odds API data to your existing race format
        """
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
            
            # Get bookmaker with the best odds (first one usually)
            if event.get('bookmakers') and len(event['bookmakers']) > 0:
                bookmaker = event['bookmakers'][0]
                markets = bookmaker.get('markets', [])
                
                if markets:
                    outcomes = markets[0].get('outcomes', [])
                    
                    for i, outcome in enumerate(outcomes):
                        # Convert decimal odds to fractional
                        decimal_odds = float(outcome.get('price', 2.0))
                        fractional_odds = self._decimal_to_fractional(decimal_odds)
                        
                        horse = {
                            'name': outcome.get('name', f'Horse {i+1}'),
                            'fractional_odds': fractional_odds,
                            'decimal_odds': decimal_odds,
                            'is_favourite': i == 0,  # First horse is usually favorite
                            'form': self._generate_form(),
                            'momentum': self._generate_momentum()
                        }
                        race['horses'].append(horse)
            
            if race['horses']:  # Only add races with horses
                races.append(race)
                
        return races
    
    def _decimal_to_fractional(self, decimal_odds):
        """Convert decimal odds to fractional format"""
        if decimal_odds <= 1:
            return "1/1"
            
        # Convert to fraction
        numerator = decimal_odds - 1
        denominator = 1
        
        # Find the closest simple fraction
        if numerator >= 1:
            # For odds >= 2.0
            whole = int(numerator)
            fraction = numerator - whole
            
            if fraction < 0.25:
                return f"{whole}/1"
            elif fraction < 0.75:
                return f"{whole * 2 + 1}/2"
            else:
                return f"{whole + 1}/1"
        else:
            # For odds < 2.0 (short odds)
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
        """Generate realistic form data"""
        forms = ['111', '211', '112', '121', '221', '311', '131', '222']
        return random.choice(forms)
    
    def _generate_momentum(self):
        """Generate momentum data"""
        momentum_values = ['Rising', 'Falling', 'Stable', 'Hot', 'Cold']
        return random.choice(momentum_values)

# Usage example in your Flask app:
"""
# In your app configuration
odds_api = TheOddsAPI(api_key='YOUR_API_KEY_HERE')

# In your route that fetches races
@app.route('/api/refresh-races')
def refresh_races():
    # Get data from The Odds API
    odds_data = odds_api.get_horse_racing_odds(sport='horse_racing_uk')
    
    # Transform to your format
    real_races = odds_api.transform_to_race_format(odds_data)
    
    # Fallback to virtual races if no real data
    if not real_races:
        real_races = generate_virtual_races()  # Your existing virtual race function
    
    # Store in your database or session
    session['races'] = real_races
    
    return jsonify({'success': True, 'races_count': len(real_races)})
"""

# Benefits of The Odds API over Betfair:
# 1. No gambling account required - perfect for virtual betting
# 2. Simple REST API - easier to integrate
# 3. Free tier with 500 requests/month
# 4. Supports multiple regions (UK, US, AU)
# 5. JSON format - no complex XML parsing
# 6. Real-time odds data
# 7. No complex authentication workflow

print("The Odds API integration example created!")
print("Key advantages for virtual betting:")
print("- No real money gambling account required")
print("- Free tier available (500 requests/month)")
print("- Simple API key authentication") 
print("- Perfect for virtual currency betting games")
