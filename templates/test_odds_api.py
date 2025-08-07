#!/usr/bin/env python3
"""
Simple test script to verify The Odds API connection
Run this after getting your API key to test the connection
"""

import requests
import json

def test_odds_api(api_key):
    """Test The Odds API connection"""
    print("🧪 Testing The Odds API Connection...")
    print("=" * 50)
    
    base_url = "https://api.the-odds-api.com/v4"
    
    # Test 1: Check available sports
    print("Test 1: Checking available sports...")
    try:
        url = f"{base_url}/sports"
        params = {'apiKey': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        sports = response.json()
        print(f"✅ Found {len(sports)} available sports")
        
        # Look for horse racing
        horse_racing_sports = [sport for sport in sports if 'horse_racing' in sport.get('key', '')]
        
        if horse_racing_sports:
            print(f"🏇 Horse racing sports available:")
            for sport in horse_racing_sports:
                print(f"   - {sport['key']}: {sport['title']}")
        else:
            print("⚠️ No horse racing sports found")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Sports API test failed: {e}")
        return False
    
    # Test 2: Try to get horse racing odds
    print("\nTest 2: Fetching horse racing odds...")
    try:
        sport_key = 'horse_racing_uk'  # Try UK horse racing first
        url = f"{base_url}/sports/{sport_key}/odds"
        params = {
            'apiKey': api_key,
            'regions': 'uk',
            'markets': 'h2h',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        events = response.json()
        print(f"✅ Found {len(events)} horse racing events")
        
        if events:
            # Show first event details
            event = events[0]
            print(f"\n📋 Sample Event:")
            print(f"   Title: {event.get('sport_title', 'Unknown')}")
            print(f"   Start: {event.get('commence_time', 'Unknown')}")
            
            if event.get('bookmakers'):
                bookmaker = event['bookmakers'][0]
                print(f"   Bookmaker: {bookmaker.get('title', 'Unknown')}")
                
                if bookmaker.get('markets'):
                    outcomes = bookmaker['markets'][0].get('outcomes', [])
                    print(f"   Runners: {len(outcomes)}")
                    
                    for i, outcome in enumerate(outcomes[:3]):  # Show first 3
                        print(f"     {i+1}. {outcome.get('name', 'Unknown')} - Odds: {outcome.get('price', 'N/A')}")
        else:
            print("ℹ️ No current events, but API is working!")
            
    except requests.RequestException as e:
        print(f"❌ Horse racing odds test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 API Test Complete - The Odds API is working!")
    print("You can now configure it in your virtual horse betting app.")
    return True

if __name__ == "__main__":
    print("The Odds API Test Tool")
    print("=" * 30)
    
    # Get API key from user
    api_key = input("Enter your The Odds API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        exit(1)
    
    # Run the test
    success = test_odds_api(api_key)
    
    if success:
        print("\n✅ Next Steps:")
        print("1. Open your virtual horse betting app")
        print("2. Go to API Configuration page") 
        print("3. Enter this API key and enable The Odds API")
        print("4. Test the connection using the app's Test API button")
    else:
        print("\n❌ Please check your API key and try again")
        print("Visit https://the-odds-api.com/ to get a valid API key")
