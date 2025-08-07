#!/usr/bin/env python3
"""
SportMonks Horse Racing API Test Script
Run this to verify your SportMonks API connection
"""

import requests
import json

def test_sportmonks_api(api_key):
    """Test SportMonks Horse Racing API connection"""
    print("🧪 Testing SportMonks Horse Racing API...")
    print("=" * 50)
    
    base_url = "https://horse-racing.sportmonks.com/api/v1"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    
    # Test 1: Check API access with courses endpoint
    print("Test 1: Checking API access...")
    try:
        url = f"{base_url}/courses"
        params = {'per_page': 5}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        courses = data.get('data', [])
        
        if courses:
            print(f"✅ API access successful! Found {len(courses)} courses")
            print(f"   Sample courses:")
            for course in courses[:3]:
                print(f"     - {course.get('name', 'Unknown')}")
        else:
            print("⚠️ API connected but no courses found")
            
    except requests.RequestException as e:
        if '401' in str(e):
            print("❌ Invalid API key. Please check your SportMonks API key.")
            return False
        elif '403' in str(e):
            print("❌ Access denied. Please check your SportMonks subscription.")
            return False
        elif '429' in str(e):
            print("❌ Rate limit exceeded. Please try again later.")
            return False
        else:
            print(f"❌ API test failed: {e}")
            return False
    
    # Test 2: Try to get horse races
    print("\nTest 2: Fetching horse racing data...")
    try:
        url = f"{base_url}/races"
        params = {
            'include': 'runners,course',
            'filter[status]': 'upcoming',
            'per_page': 3
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        races = data.get('data', [])
        
        if races:
            print(f"✅ Found {len(races)} upcoming races")
            
            # Show details of first race
            race = races[0]
            print(f"\n📋 Sample Race:")
            print(f"   Name: {race.get('name', 'Unknown Race')}")
            print(f"   Start: {race.get('starts_at', 'Unknown')}")
            print(f"   Course: {race.get('course', {}).get('name', 'Unknown')}")
            
            runners = race.get('runners', [])
            if runners:
                print(f"   Runners: {len(runners)}")
                for i, runner in enumerate(runners[:3]):  # Show first 3
                    print(f"     {i+1}. {runner.get('name', f'Horse {i+1}')}")
            else:
                print(f"   Runners: Data structure may vary, checking included...")
                included = data.get('included', [])
                runner_count = sum(1 for item in included if item.get('type') == 'runners')
                print(f"   Found {runner_count} runners in included data")
        else:
            print("ℹ️ No upcoming races found, but API is working!")
            print("   This is normal if there are no scheduled races right now.")
            
    except requests.RequestException as e:
        print(f"❌ Horse racing data test failed: {e}")
        return False
    
    # Test 3: Check account limits
    print("\nTest 3: Checking API usage...")
    try:
        # The response headers usually contain rate limit info
        if hasattr(response, 'headers'):
            rate_limit = response.headers.get('X-RateLimit-Limit', 'Unknown')
            rate_remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
            
            print(f"   Daily limit: {rate_limit}")
            print(f"   Remaining today: {rate_remaining}")
        else:
            print("   Rate limit info not available in headers")
            
    except Exception as e:
        print(f"   Could not retrieve usage info: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 SportMonks API Test Complete!")
    print("Your API is working and ready for integration.")
    return True

if __name__ == "__main__":
    print("SportMonks Horse Racing API Test Tool")
    print("=" * 40)
    
    # Get API key from user
    api_key = input("Enter your SportMonks API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        exit(1)
    
    # Run the test
    success = test_sportmonks_api(api_key)
    
    if success:
        print("\n✅ Next Steps:")
        print("1. Open your virtual horse betting app")
        print("2. Go to API Configuration page") 
        print("3. Enter this API key and enable SportMonks API")
        print("4. Test the connection using the app's Test API button")
        print("5. Choose your preferred region (UK, US, AU, IE)")
    else:
        print("\n❌ Please check your API key and try again")
        print("Visit https://www.sportmonks.com/horse-racing-api to get a valid API key")
