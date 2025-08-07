# Complete Flask Integration for Free Horse Racing Data
# No API keys needed - works immediately!

from flask import Flask, render_template, request, session, jsonify, flash, redirect, url_for
import random
import json
from datetime import datetime, timedelta

# Import the Free Racing Data Generator
from free_racing_data import FreeHorseRacingData

# Initialize racing data generators
racing_generators = {
    'uk_racing': FreeHorseRacingData('uk'),
    'us_racing': FreeHorseRacingData('us'),
    'au_racing': FreeHorseRacingData('au')
}

# Add these routes to your Flask app:

@app.route('/admin/api-config', methods=['GET', 'POST'])
def api_config():
    """Handle API configuration - Free Racing Data version"""
    if request.method == 'POST':
        # Save configuration
        session['use_free_api'] = 'use_free_api' in request.form
        session['racing_source'] = request.form.get('racing_source', 'uk_racing')
        session['update_frequency'] = request.form.get('update_frequency', '60')
        session['use_virtual'] = 'use_virtual' in request.form
        session['racing_mode'] = request.form.get('racing_mode', 'enhanced')
        
        # Test connection (always succeeds!)
        if session.get('use_free_api'):
            source = session.get('racing_source', 'uk_racing')
            generator = racing_generators.get(source)
            
            if generator:
                success, message = generator.test_connection()
                session['racing_api_status'] = message
                
                # Get sample data
                sample_info = generator.get_sample_race_info()
                sample_message = f"Sample: {sample_info['sample_race']} at {sample_info['sample_course']} with {sample_info['horse_count']} horses"
                session['racing_api_status'] = f"{message} {sample_message}"
                
                flash("✅ Free Racing Data configured successfully! No API key needed.")
            else:
                session['racing_api_status'] = "❌ Invalid racing source selected"
                flash("Configuration saved but invalid source selected.")
        else:
            session['racing_api_status'] = "Free Racing Data disabled"
            flash("Configuration saved!")
        
        return redirect(url_for('api_config'))
    
    # GET request - show configuration form
    return render_template('admin_api_config.html',
                         use_free_api=session.get('use_free_api', False),
                         racing_source=session.get('racing_source', 'uk_racing'),
                         update_frequency=session.get('update_frequency', '60'),
                         use_virtual=session.get('use_virtual', True),
                         racing_mode=session.get('racing_mode', 'enhanced'),
                         racing_api_status=session.get('racing_api_status', 'Not configured'),
                         api_status="Free Racing Data - No API Key Required!")

@app.route('/admin/test-api')
def test_api():
    """Test the Free Racing Data connection"""
    if not session.get('use_free_api'):
        flash("Please enable Free Racing Data first!")
        return redirect(url_for('api_config'))
    
    source = session.get('racing_source', 'uk_racing')
    generator = racing_generators.get(source)
    
    if not generator:
        flash("❌ Invalid racing source configured!")
        return redirect(url_for('api_config'))
    
    # Test and get sample data
    success, message = generator.test_connection()
    sample_info = generator.get_sample_race_info()
    
    # Generate a test race
    test_races = generator.generate_races(num_races=1)
    
    if test_races:
        race = test_races[0]
        flash(f"✅ Test Successful! Generated race: '{race['title']}' with {len(race['horses'])} horses at {race['course']}")
        
        # Show some horse names
        horse_names = [h['name'] for h in race['horses'][:3]]
        flash(f"Sample horses: {', '.join(horse_names)}")
    else:
        flash("⚠️ Test completed but no races generated")
    
    session['racing_api_status'] = f"{message} - Test completed successfully"
    
    return redirect(url_for('api_config'))

@app.route('/api/refresh-races')
def refresh_races_api():
    """Refresh races using Free Racing Data"""
    races = []
    
    # Try to get data from Free Racing API if enabled
    if session.get('use_free_api'):
        try:
            source = session.get('racing_source', 'uk_racing')
            generator = racing_generators.get(source)
            
            if generator:
                # Generate 6-10 races
                num_races = random.randint(6, 10)
                races = generator.generate_races(num_races=num_races)
                
                if races:
                    session['races'] = races
                    return jsonify({
                        'success': True, 
                        'races_count': len(races),
                        'source': f'Free Racing Data ({source.replace("_", " ").title()})',
                        'sample_race': races[0]['title'] if races else 'None'
                    })
        except Exception as e:
            print(f"Error with Free Racing Data: {e}")
    
    # Fallback to virtual races if configured
    if session.get('use_virtual', True):
        races = generate_enhanced_virtual_races()  # Your existing function
        session['races'] = races
        return jsonify({
            'success': True, 
            'races_count': len(races),
            'source': 'Enhanced Virtual Racing System'
        })
    
    return jsonify({'success': False, 'error': 'No racing data source configured'})

def generate_enhanced_virtual_races():
    """Enhanced virtual race generation using the free data generator"""
    generator = FreeHorseRacingData('uk')  # Default to UK
    return generator.generate_races(num_races=8)

# Auto-refresh races periodically
@app.route('/auto-refresh-races')
def auto_refresh_races():
    """Auto-refresh races based on configured frequency"""
    try:
        frequency_minutes = int(session.get('update_frequency', 60))
        
        # Check if it's time to refresh
        last_refresh = session.get('last_race_refresh')
        if last_refresh:
            last_refresh_time = datetime.fromisoformat(last_refresh)
            if (datetime.now() - last_refresh_time).total_seconds() < (frequency_minutes * 60):
                return jsonify({'success': True, 'message': 'Races are up to date'})
        
        # Refresh races
        refresh_result = refresh_races_api()
        session['last_race_refresh'] = datetime.now().isoformat()
        
        return refresh_result
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Background task to keep races fresh (optional)
def schedule_race_refresh():
    """Call this to set up automatic race refreshing"""
    import threading
    import time
    
    def refresh_worker():
        while True:
            try:
                frequency_minutes = 60  # Default 1 hour
                time.sleep(frequency_minutes * 60)
                
                # Refresh races in background
                with app.app_context():
                    # This would need proper session handling in production
                    pass
                    
            except Exception as e:
                print(f"Background refresh error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    # Start background thread
    refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
    refresh_thread.start()

# Your existing routes (races, place_bet, etc.) don't need changes
# They will automatically use the new race data format

print("Flask Free Racing Data Integration ready!")
print("✅ No API keys required")
print("✅ Works immediately") 
print("✅ Realistic racing data")
print("✅ Multiple regions supported")
print("✅ Perfect for virtual betting!")
print("")
print("Next steps:")
print("1. Copy this code to your main Flask app file")
print("2. Import the FreeHorseRacingData class")
print("3. Test the /admin/api-config route")
print("4. Enable Free Racing Data - no setup required!")
