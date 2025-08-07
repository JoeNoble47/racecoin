from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import traceback
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
from datetime import datetime, timedelta, date
from fractions import Fraction
import requests
import json

os.environ['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'development')

app = Flask(__name__)

# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # HTTPS in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ----- API Configuration -----
API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_config.json")

# Betfair Exchange API Configuration
BETFAIR_APP_KEY = "YOUR_BETFAIR_APP_KEY"
BETFAIR_USERNAME = "YOUR_BETFAIR_USERNAME"
BETFAIR_PASSWORD = "YOUR_BETFAIR_PASSWORD"
BETFAIR_SESSION_TOKEN = None
BETFAIR_BASE_URL = "https://api.betfair.com/exchange/betting/rest/v1.0"
BETFAIR_LOGIN_URL = "https://identitysso.betfair.com/api/login"

# Racing Data Configuration
USE_BETFAIR_API = False
USE_VIRTUAL_RACING = True
ENHANCED_VIRTUAL_MODE = True

# ----- BRANDING CONFIGURATION -----
APP_NAME = "RaceCoin"
APP_TAGLINE = "Virtual Horse Racing & Betting"
APP_DESCRIPTION = "The ultimate virtual horse racing experience with realistic odds, achievements, and competitive leaderboards"
CURRENCY_NAME = "RaceCoins"
CURRENCY_SYMBOL = "RC"
APP_VERSION = "2.0"
APP_AUTHOR = "RaceCoin Gaming"

def load_api_config():
    """Load API configuration from file"""
    global BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD, USE_BETFAIR_API
    
    try:
        if os.path.exists(API_CONFIG_FILE):
            with open(API_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
                # Betfair configuration
                BETFAIR_APP_KEY = config.get('betfair_app_key', 'YOUR_BETFAIR_APP_KEY')
                BETFAIR_USERNAME = config.get('betfair_username', 'YOUR_BETFAIR_USERNAME')
                BETFAIR_PASSWORD = config.get('betfair_password', 'YOUR_BETFAIR_PASSWORD')
                USE_BETFAIR_API = config.get('use_betfair_api', False)
                
                return (
                    config.get('use_virtual_racing', True),
                    config.get('racing_mode', 'enhanced')
                )
    except Exception as e:
        print(f"Error loading config: {e}")
    return True, 'enhanced'

def save_api_config(use_virtual_racing=True, racing_mode='enhanced', 
                   betfair_app_key=None, betfair_username=None, betfair_password=None, use_betfair_api=False):
    """Save API configuration to file"""
    try:
        config = {
            'use_virtual_racing': use_virtual_racing,
            'racing_mode': racing_mode,
            'use_betfair_api': use_betfair_api,
            'betfair_app_key': betfair_app_key or BETFAIR_APP_KEY,
            'betfair_username': betfair_username or BETFAIR_USERNAME,
            'betfair_password': betfair_password or BETFAIR_PASSWORD
        }
        with open(API_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")

# Load configuration on startup
USE_VIRTUAL_RACING, RACING_MODE = load_api_config()
print(f"DEBUG: Loaded API config - BETFAIR_API={USE_BETFAIR_API}, VIRTUAL_RACING={USE_VIRTUAL_RACING}, MODE={RACING_MODE}")

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

# ----- XP/Rank System -----
XP_PER_LEVEL = 100

RANKS = [
    (1, "Rookie"),
    (10, "Amateur"),
    (20, "Pro"),
    (40, "Champion"),
    (100, "Legend")
]

def get_number_rank(xp, xp_per_level=XP_PER_LEVEL):
    return (xp // xp_per_level) + 1

def get_rank_title(number_rank):
    for threshold, name in reversed(RANKS):
        if number_rank >= threshold:
            return name
    return "Rookie"

def calculate_xp(win_amount, current_streak, acca_win=0):
    base_xp = 10 + (win_amount // 10)
    streak_bonus = current_streak * 5
    acca_bonus = acca_win // 50
    return base_xp + streak_bonus + acca_bonus

def migrate_add_xp_and_rank_and_login_bonus_and_achievements():
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN rank TEXT DEFAULT 'Rookie'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN login_streak INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # Achievements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            code TEXT,
            name TEXT,
            unlocked_on TEXT,
            reward INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def update_user_xp_and_rank(user_id, earned_xp):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    xp = row["xp"] if row and "xp" in row.keys() else 0
    new_xp = xp + earned_xp
    number_rank = get_number_rank(new_xp)
    rank_title = get_rank_title(number_rank)
    c.execute("UPDATE users SET xp = ?, rank = ? WHERE id = ?", (new_xp, rank_title, user_id))
    conn.commit()
    conn.close()
# ----- End XP/Rank System -----

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
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            highest_accumulator INTEGER DEFAULT 0,
            total_bets INTEGER DEFAULT 0,
            biggest_single_win INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            rank TEXT DEFAULT 'Rookie',
            last_login TEXT,
            login_streak INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()
migrate_add_xp_and_rank_and_login_bonus_and_achievements()

def update_user_coins(user_id, coins):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET coins = ? WHERE id = ?", (coins, user_id))
    conn.commit()
    conn.close()

# ----- Odds Conversion -----
STANDARD_FRACTIONS = [
    (1.05, "1/20"), (1.1, "1/10"), (1.2, "1/5"), (1.25, "1/4"), (1.33, "1/3"),
    (1.5, "1/2"), (1.57, "4/7"), (1.67, "4/6"), (1.73, "8/11"), (1.8, "4/5"),
    (1.91, "10/11"), (2.0, "Evs"), (2.1, "11/10"), (2.25, "5/4"), (2.38, "11/8"),
    (2.5, "6/4"), (2.63, "13/8"), (2.75, "7/4"), (3.0, "2/1"), (3.5, "5/2"),
    (4.0, "3/1"), (4.5, "7/2"), (5.0, "4/1"), (6.0, "5/1"), (7.0, "6/1"),
    (8.0, "7/1"), (9.0, "8/1"), (10.0, "9/1"), (11.0, "10/1"), (13.0, "12/1"),
    (15.0, "14/1"), (17.0, "16/1"), (21.0, "20/1"), (26.0, "25/1"), (34.0, "33/1"),
    (51.0, "50/1"), (67.0, "66/1"), (101.0, "100/1")
]

def decimal_to_nearest_fraction(decimal_odds):
    target = decimal_odds
    closest = min(STANDARD_FRACTIONS, key=lambda x: abs(x[0] - target))
    return closest[1]
# ----- End Odds Conversion -----

# ----- Achievements System -----
ACHIEVEMENTS = [
    # (code, name, reward, condition, icon, description)
    ("first_bet", "First Bet", 200, lambda user: user["total_bets"] >= 1, "🎲", "Place your first bet"),
    ("first_win", "First Win", 300, lambda user: user["wins"] >= 1, "🏇", "Win your first race"),
    ("five_wins", "5 Wins", 500, lambda user: user["wins"] >= 5, "🥉", "Win 5 races"),
    ("ten_wins", "10 Wins", 1000, lambda user: user["wins"] >= 10, "🏅", "Win 10 races"),
    ("twentyfive_wins", "25 Wins", 2500, lambda user: user["wins"] >= 25, "🥈", "Win 25 races"),
    ("fifty_wins", "50 Wins", 5000, lambda user: user["wins"] >= 50, "🥇", "Win 50 races"),
    ("hundred_wins", "100 Wins", 12000, lambda user: user["wins"] >= 100, "🏆", "Win 100 races"),
    ("first_acca", "First Acca Win", 800, lambda user: user["highest_accumulator"] > 0, "🎯", "Win your first accumulator bet"),
    ("three_acca", "3 Acca Wins", 2000, lambda user: user.get("acca_wins", 0) >= 3, "💎", "Win 3 accumulator bets"),
    ("ten_acca", "10 Acca Wins", 7500, lambda user: user.get("acca_wins", 0) >= 10, "💰", "Win 10 accumulator bets"),
    ("biggest_win", "RaceCoin Millionaire", 2000, lambda user: user["biggest_single_win"] >= 1000, "💵", "Win 1,000+ RaceCoins in a single bet"),
    ("first_streak", "5-Day Login Streak", 300, lambda user: user["login_streak"] >= 5, "🔥", "Log in 5 days in a row"),
    ("ten_streak", "10-Day Login Streak", 1000, lambda user: user["login_streak"] >= 10, "🌟", "Log in 10 days in a row"),
    ("thirty_streak", "30-Day Login Streak", 4000, lambda user: user["login_streak"] >= 30, "🏅", "Log in 30 days in a row"),
    ("level_10", "Reach Level 10", 1000, lambda user: user["number_rank"] >= 10, "🔟", "Reach Level 10"),
    ("level_20", "Reach Level 20", 2500, lambda user: user["number_rank"] >= 20, "2️⃣0️⃣", "Reach Level 20"),
    ("level_40", "Reach Level 40", 7000, lambda user: user["number_rank"] >= 40, "4️⃣0️⃣", "Reach Level 40"),
    ("level_100", "Reach Level 100", 25000, lambda user: user["number_rank"] >= 100, "💯", "Reach Level 100"),
]

def get_unlocked_achievements(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT code, name, unlocked_on, reward FROM achievements WHERE user_id = ?", (user_id,))
    achievements = [dict(row) for row in c.fetchall()]
    conn.close()
    code_map = {a[0]: a for a in ACHIEVEMENTS}
    for ach in achievements:
        achdef = code_map.get(ach["code"])
        if achdef:
            ach["icon"] = achdef[4]
            ach["description"] = achdef[5]
    return achievements

def has_achievement(user_id, code):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT 1 FROM achievements WHERE user_id = ? AND code = ?", (user_id, code))
    res = c.fetchone()
    conn.close()
    return res is not None

def unlock_achievement(user_id, code, name, reward):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO achievements (user_id, code, name, unlocked_on, reward) VALUES (?, ?, ?, ?, ?)",
              (user_id, code, name, now, reward))
    c.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (reward, user_id))
    conn.commit()
    conn.close()

def count_acca_wins(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM achievements WHERE user_id = ? AND code IN ('first_acca', 'three_acca', 'ten_acca')", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def check_and_award_achievements(user_id, user_dict):
    user_dict = dict(user_dict)
    user_dict["acca_wins"] = user_dict.get("acca_wins", 0)
    user_dict["number_rank"] = get_number_rank(user_dict.get("xp", 0))
    unlocked = []
    for code, name, reward, condition, icon, description in ACHIEVEMENTS:
        if not has_achievement(user_id, code) and condition(user_dict):
            unlock_achievement(user_id, code, name, reward)
            unlocked.append((name, reward))
    return unlocked

# ----- User Stats Update Function -----
def update_user_stats(user_id, won=False, win_amount=0, acca_win=0):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT wins, current_streak, longest_streak, highest_accumulator, total_bets, biggest_single_win, xp FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    wins, current_streak, longest_streak, highest_accumulator, total_bets, biggest_single_win, xp = (
        row["wins"], row["current_streak"], row["longest_streak"], row["highest_accumulator"], row["total_bets"], row["biggest_single_win"], row["xp"]
    )
    total_bets += 1
    earned_xp = 0
    if won:
        wins += 1
        current_streak += 1
        if current_streak > longest_streak:
            longest_streak = current_streak
        if win_amount > biggest_single_win:
            biggest_single_win = win_amount
        earned_xp = calculate_xp(win_amount, current_streak, acca_win)
    else:
        current_streak = 0
    if acca_win > highest_accumulator:
        highest_accumulator = acca_win
    c.execute("""
        UPDATE users
        SET wins = ?, current_streak = ?, longest_streak = ?, highest_accumulator = ?, total_bets = ?, biggest_single_win = ?
        WHERE id = ?
    """, (wins, current_streak, longest_streak, highest_accumulator, total_bets, biggest_single_win, user_id))
    if earned_xp > 0:
        new_xp = xp + earned_xp
        number_rank = get_number_rank(new_xp)
        rank_title = get_rank_title(number_rank)
        c.execute("UPDATE users SET xp = ?, rank = ? WHERE id = ?", (new_xp, rank_title, user_id))
    conn.commit()
    conn.close()
# ----- End User Stats Update Function -----

def make_user_admin(username):
    """Make a user an admin (use this function in Python console if needed)"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    affected_rows = c.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def load_leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, coins, wins, current_streak, longest_streak, highest_accumulator, total_bets, biggest_single_win, xp, rank, login_streak
        FROM users
        ORDER BY coins DESC
    """)
    data = c.fetchall()
    conn.close()
    leaderboard = []
    for row in data:
        user_dict = dict(row)
        xp = user_dict.get("xp", 0)
        user_dict["number_rank"] = get_number_rank(xp)
        user_dict["rank_title"] = get_rank_title(user_dict["number_rank"])
        user_dict["achievements"] = get_unlocked_achievements(user_dict["id"])
        leaderboard.append(user_dict)
    return leaderboard

def update_leaderboard(username, coins):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET coins = ? WHERE username = ?", (coins, username))
    conn.commit()
    conn.close()

# ----- DAILY LOGIN BONUS SYSTEM -----
DAILY_BONUS_BASE = 100
DAILY_BONUS_STREAK_BONUS = 20
def give_daily_bonus(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT coins, last_login, login_streak FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    coins = row["coins"]
    last_login = row["last_login"]
    login_streak = row["login_streak"] if row["login_streak"] else 0
    today = date.today()
    bonus_given = False
    bonus = 0
    last_login_date = None
    if last_login:
        try:
            last_login_date = datetime.strptime(last_login, "%Y-%m-%d").date()
        except Exception:
            last_login_date = None
    if last_login_date == today:
        pass
    else:
        if last_login_date == today - timedelta(days=1):
            login_streak += 1
        else:
            login_streak = 1
        bonus = DAILY_BONUS_BASE + (login_streak - 1) * DAILY_BONUS_STREAK_BONUS
        coins += bonus
        c.execute("UPDATE users SET coins = ?, last_login = ?, login_streak = ? WHERE id = ?",
                  (coins, today.strftime("%Y-%m-%d"), login_streak, user_id))
        conn.commit()
        bonus_given = True
    conn.close()
    return {
        "bonus_given": bonus_given,
        "bonus": bonus,
        "login_streak": login_streak
    }
# ----- END DAILY LOGIN BONUS SYSTEM -----

# ----- VIRTUAL RACE DATA FUNCTIONS -----
def fetch_horse_racing_events():
    """Fetch horse racing events from Betfair API or generate virtual races"""
    print(f"DEBUG: USE_BETFAIR_API={USE_BETFAIR_API}, USE_VIRTUAL_RACING={USE_VIRTUAL_RACING}, MODE={RACING_MODE}")
    
    # Try Betfair API first if enabled
    if USE_BETFAIR_API:
        print("DEBUG: Attempting to fetch from Betfair API...")
        try:
            betfair_races = fetch_betfair_horse_racing_events()
            if betfair_races:
                print(f"DEBUG: ✅ Using {len(betfair_races)} races from Betfair API")
                return betfair_races
            else:
                print("DEBUG: Betfair API returned no races, falling back to virtual")
        except Exception as e:
            print(f"DEBUG: Betfair API error: {e}, falling back to virtual")
    
    # Fall back to virtual racing
    if not USE_VIRTUAL_RACING:
        print("DEBUG: Virtual racing disabled and no API data available")
        return None
    
    try:
        if RACING_MODE == 'enhanced':
            return fetch_enhanced_virtual_races()
        else:
            return fetch_demo_race_data()
        
    except Exception as e:
        print(f"Unexpected error generating virtual races: {e}")
        return None

def fetch_enhanced_virtual_races():
    """Generate enhanced virtual race data with realistic features"""
    import time
    from datetime import datetime, timedelta
    
    print("DEBUG: Generating enhanced virtual races")
    
    # Real UK racecourses with realistic meeting types
    racecourses = [
        {'name': 'Ascot', 'type': 'Flat', 'prestige': 'high'},
        {'name': 'Cheltenham', 'type': 'National Hunt', 'prestige': 'high'},
        {'name': 'Newmarket', 'type': 'Flat', 'prestige': 'high'},
        {'name': 'York', 'type': 'Flat', 'prestige': 'high'},
        {'name': 'Aintree', 'type': 'National Hunt', 'prestige': 'medium'},
        {'name': 'Goodwood', 'type': 'Flat', 'prestige': 'medium'},
        {'name': 'Doncaster', 'type': 'Flat', 'prestige': 'medium'},
        {'name': 'Chester', 'type': 'Flat', 'prestige': 'medium'},
        {'name': 'Bath', 'type': 'Flat', 'prestige': 'low'},
        {'name': 'Lingfield', 'type': 'All Weather', 'prestige': 'low'}
    ]
    
    # Realistic horse name components
    horse_prefixes = [
        'Royal', 'Golden', 'Silver', 'Thunder', 'Lightning', 'Storm', 'Fire', 'Wind',
        'Star', 'Moon', 'Diamond', 'Emerald', 'Crystal', 'Shadow', 'Midnight', 'Dawn',
        'Swift', 'Bold', 'Brave', 'Noble', 'Mighty', 'Dancing', 'Flying', 'Racing'
    ]
    
    horse_suffixes = [
        'Dancer', 'Runner', 'Flash', 'Spirit', 'Warrior', 'Knight', 'Prince', 'King',
        'Queen', 'Lady', 'Lord', 'Master', 'Champion', 'Winner', 'Glory', 'Pride',
        'Arrow', 'Bullet', 'Storm', 'Thunder', 'Lightning', 'Star', 'Dream', 'Hope'
    ]
    
    # Generate realistic races
    virtual_races = []
    base_time = datetime.now()
    
    for i in range(4):  # Generate 4 races
        racecourse = random.choice(racecourses)
        race_time = base_time + timedelta(hours=i+1, minutes=random.randint(0, 45))
        
        # Generate horses for this race (6-12 runners is realistic)
        num_horses = random.randint(6, 12)
        horses = []
        
        for j in range(num_horses):
            prefix = random.choice(horse_prefixes)
            suffix = random.choice(horse_suffixes)
            horse_name = f"{prefix} {suffix}"
            
            # Ensure unique names
            counter = 1
            original_name = horse_name
            while horse_name in horses:
                horse_name = f"{original_name} {counter}"
                counter += 1
            
            horses.append(horse_name)
        
        # Generate realistic odds based on field size and horse position
        race_data = {
            'id': f"virtual_{int(time.time())}_{i}",
            'meeting_name': f"{racecourse['name']} ({racecourse['type']})",
            'start_time': race_time.isoformat(),
            'track': racecourse['name'],
            'race_number': i + 1,
            'race_type': racecourse['type'],
            'is_real_race': False,
            'data_source': 'Enhanced Virtual',
            'runners': []
        }
        
        for idx, horse in enumerate(horses):
            # More realistic odds distribution
            if idx == 0:  # Favorite
                odds = round(random.uniform(2.0, 4.0), 2)
            elif idx == 1:  # Second favorite
                odds = round(random.uniform(3.0, 6.0), 2)
            elif idx < 4:  # Other contenders
                odds = round(random.uniform(4.0, 8.0), 2)
            else:  # Outsiders
                odds = round(random.uniform(6.0, 25.0), 2)
            
            race_data['runners'].append({
                'name': horse,
                'number': idx + 1,
                'odds': {
                    'decimal': odds
                },
                'form': generate_horse_form(),
                'jockey': generate_jockey_name(),
                'weight': f"{random.randint(8, 10)}-{random.randint(0, 13)}"
            })
        
        virtual_races.append(race_data)
    
    print(f"DEBUG: ✅ Generated {len(virtual_races)} enhanced virtual races")
    return virtual_races

def generate_horse_form():
    """Generate realistic horse form string"""
    form_chars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'F', 'P', 'U']
    return ''.join(random.choices(form_chars, k=5))

def generate_jockey_name():
    """Generate realistic jockey names"""
    first_names = ['James', 'Ryan', 'Frankie', 'William', 'Oisin', 'Tom', 'Hollie', 'Hayley', 'Jim', 'Paul']
    last_names = ['Smith', 'Murphy', 'Dettori', 'Buick', 'Moore', 'Marquand', 'Doyle', 'Turner', 'Crowley', 'Hanagan']
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def fetch_demo_race_data():
    """Generate realistic demo race data without API calls"""
    import random
    from datetime import datetime, timedelta
    
    print("DEBUG: Generating demo race data with realistic horse names and tracks")
    
    # Real UK race tracks
    tracks = [
        "Ascot", "Cheltenham", "Newmarket", "York", "Goodwood", 
        "Epsom", "Aintree", "Doncaster", "Chester", "Bath"
    ]
    
    # Realistic horse names (inspired by real racing)
    horse_name_parts = {
        'first': ['Royal', 'Golden', 'Silver', 'Thunder', 'Lightning', 'Storm', 'Fire', 'Wind', 
                 'Star', 'Moon', 'Sun', 'Diamond', 'Emerald', 'Ruby', 'Crystal', 'Shadow'],
        'second': ['Dancer', 'Runner', 'Flash', 'Spirit', 'Warrior', 'Knight', 'Prince', 'King',
                  'Queen', 'Lady', 'Lord', 'Master', 'Champion', 'Winner', 'Glory', 'Pride']
    }
    
    demo_races = []
    base_time = datetime.now()
    
    for i in range(4):  # Generate 4 demo races
        track = random.choice(tracks)
        race_time = base_time + timedelta(hours=i+1, minutes=random.randint(0, 45))
        
        # Generate horses for this race
        horses = []
        for j in range(random.randint(6, 10)):  # 6-10 horses per race
            first = random.choice(horse_name_parts['first'])
            second = random.choice(horse_name_parts['second'])
            horse_name = f"{first} {second}"
            
            # Avoid duplicates
            counter = 1
            original_name = horse_name
            while horse_name in horses:
                horse_name = f"{original_name} {counter}"
                counter += 1
            
            horses.append(horse_name)
        
        race_data = {
            'id': 1000 + i,  # Use integer IDs starting from 1000 for demo races
            'meeting_name': f"{track} Racecourse",
            'start_time': race_time.isoformat(),
            'track': track,
            'race_number': i + 1,
            'runners': [
                {
                    'name': horse,
                    'number': idx + 1,
                    'odds': {
                        'decimal': round(random.uniform(2.0, 12.0), 2)
                    }
                }
                for idx, horse in enumerate(horses)
            ]
        }
        
        demo_races.append(race_data)
    
    print(f"DEBUG: Generated {len(demo_races)} demo races with real track names")
    return demo_races

def convert_rapidapi_race_to_game_format(race_data):
    """Convert RapidAPI Horse Racing data to our game format"""
    try:
        # Extract race information
        race_id = race_data.get('id', f"rapid_{random.randint(1000, 9999)}")
        race_title = race_data.get('meeting_name', 'Horse Racing')
        race_time = race_data.get('start_time', datetime.now().isoformat())
        
        # Extract horses and create odds
        horses = []
        horse_odds = {}
        
        # Get runners from the race
        runners = race_data.get('runners', [])
        if runners:
            for runner in runners[:8]:  # Limit to 8 horses
                horse_name = runner.get('name', f"Horse #{len(horses)+1}")
                horses.append(horse_name)
                
                # Use API odds if available, otherwise generate realistic odds
                odds = runner.get('odds', {})
                if odds and 'decimal' in odds:
                    decimal_odds = float(odds['decimal'])
                else:
                    # Generate odds based on runner number (lower numbers often favored)
                    runner_num = runner.get('number', len(horses))
                    if runner_num <= 2:
                        decimal_odds = round(random.uniform(2.0, 4.0), 2)  # Favorites
                    elif runner_num <= 4:
                        decimal_odds = round(random.uniform(3.5, 7.0), 2)  # Mid-range
                    else:
                        decimal_odds = round(random.uniform(6.0, 15.0), 2)  # Outsiders
                
                horse_odds[horse_name] = decimal_odds
        
        # Fallback if no runners found
        if not horses:
            horses = [
                "Thunder Bolt", "Lightning Strike", "Storm Runner", 
                "Fire Flash", "Wind Walker", "Star Gazer", 
                "Golden Arrow", "Silver Bullet"
            ]
            for horse in horses:
                horse_odds[horse] = round(random.uniform(2.0, 8.0), 2)
        
        # Ensure minimum horses
        while len(horses) < 5:
            horses.append(f"Mystery Horse {len(horses)+1}")
            horse_odds[horses[-1]] = round(random.uniform(4.0, 10.0), 2)
        
        return {
            'id': race_id,
            'horses': horses[:8],  # Max 8 horses
            'odds': horse_odds,
            'title': race_title,
            'start_time': race_time,
            'is_real_race': True,
            'track': race_data.get('track', 'Unknown Track'),
            'race_number': race_data.get('race_number', 1)
        }
        
    except Exception as e:
        print(f"Error converting RapidAPI race data: {e}")
        return None

def convert_api_race_to_game_format(event_data, odds_data=None):
    """Convert API race data to our game's race format (legacy function)"""
    # Check if this is RapidAPI format
    if 'meeting_name' in event_data or 'runners' in event_data:
        return convert_rapidapi_race_to_game_format(event_data)
    
    # Original conversion logic for other APIs
    try:
        race_id = event_data.get('id', f"api_{random.randint(1000, 9999)}")
        race_time = event_data.get('commence_time', datetime.now().isoformat())
        race_title = event_data.get('sport_title', 'Horse Racing')
        
        horses = ["Thunder Bolt", "Lightning Strike", "Storm Runner", "Fire Flash", "Wind Walker"]
        horse_odds = {horse: round(random.uniform(2.0, 8.0), 2) for horse in horses}
        
        return {
            'id': race_id,
            'horses': horses,
            'odds': horse_odds,
            'title': race_title,
            'start_time': race_time,
            'is_real_race': True
        }
        
    except Exception as e:
        print(f"Error converting API race data: {e}")
        return None

def get_real_races():
    """Get real horse racing events, fallback to virtual if API fails"""
    try:
        events = fetch_horse_racing_events()
        if not events:
            return None
        
        real_races = []
        
        # Handle different response formats
        if isinstance(events, list):
            race_list = events
        elif isinstance(events, dict) and 'races' in events:
            race_list = events['races']
        elif isinstance(events, dict) and 'data' in events:
            race_list = events['data']
        else:
            race_list = [events] if events else []
        
        for event in race_list[:5]:  # Limit to 5 races
            race_data = convert_api_race_to_game_format(event)
            if race_data:
                real_races.append(race_data)
                print(f"DEBUG: Added real race: {race_data['title']}")
        
        return real_races if real_races else None
        
    except Exception as e:
        print(f"Error getting real races: {e}")
        return None
# ----- END REAL RACE DATA API FUNCTIONS -----

# ----- BETFAIR EXCHANGE API FUNCTIONS -----
def betfair_login():
    """Login to Betfair and get session token"""
    global BETFAIR_SESSION_TOKEN
    
    if not BETFAIR_APP_KEY or BETFAIR_APP_KEY == "YOUR_BETFAIR_APP_KEY":
        print("Betfair App Key not configured")
        return False
    
    try:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Application': BETFAIR_APP_KEY
        }
        
        data = {
            'username': BETFAIR_USERNAME,
            'password': BETFAIR_PASSWORD
        }
        
        response = requests.post(BETFAIR_LOGIN_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            login_response = response.json()
            if login_response.get('status') == 'SUCCESS':
                BETFAIR_SESSION_TOKEN = login_response.get('token')
                print("✅ Betfair login successful")
                return True
            else:
                print(f"❌ Betfair login failed: {login_response.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Betfair login HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Betfair login exception: {e}")
        return False

def betfair_api_request(endpoint, params=None):
    """Make authenticated request to Betfair API"""
    if not BETFAIR_SESSION_TOKEN:
        if not betfair_login():
            return None
    
    headers = {
        'Content-Type': 'application/json',
        'X-Application': BETFAIR_APP_KEY,
        'X-Authentication': BETFAIR_SESSION_TOKEN,
        'Accept': 'application/json'
    }
    
    url = f"{BETFAIR_BASE_URL}/{endpoint}/"
    
    try:
        if params:
            response = requests.post(url, headers=headers, json=params, timeout=10)
        else:
            response = requests.post(url, headers=headers, json={}, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Betfair API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Betfair API request error: {e}")
        return None

def fetch_betfair_horse_racing_events():
    """Fetch horse racing events from Betfair Exchange API"""
    print("DEBUG: Fetching horse racing events from Betfair...")
    
    # Get horse racing event types
    event_types = betfair_api_request('listEventTypes', {
        'filter': {
            'textQuery': 'Horse Racing'
        }
    })
    
    if not event_types:
        print("Failed to get Betfair event types")
        return None
    
    horse_racing_type_id = None
    for event_type in event_types:
        if 'Horse Racing' in event_type.get('eventType', {}).get('name', ''):
            horse_racing_type_id = event_type.get('eventType', {}).get('id')
            break
    
    if not horse_racing_type_id:
        print("Horse Racing event type not found")
        return None
    
    # Get today's horse racing events
    today = datetime.now().strftime('%Y-%m-%dT00:00:00.000Z')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z')
    
    events = betfair_api_request('listEvents', {
        'filter': {
            'eventTypeIds': [horse_racing_type_id],
            'marketStartTime': {
                'from': today,
                'to': tomorrow
            }
        }
    })
    
    if not events:
        print("No Betfair events found")
        return None
    
    betfair_races = []
    
    # Get markets for each event (limit to first 4 events)
    for event in events[:4]:
        event_id = event.get('event', {}).get('id')
        event_name = event.get('event', {}).get('name', 'Horse Racing')
        
        markets = betfair_api_request('listMarketCatalogue', {
            'filter': {
                'eventIds': [event_id],
                'marketTypeCodes': ['WIN']  # Win markets only
            },
            'maxResults': 1,
            'marketProjection': ['RUNNER_DESCRIPTION', 'MARKET_START_TIME']
        })
        
        if markets:
            market = markets[0]
            market_id = market.get('marketId')
            
            # Get current odds
            market_book = betfair_api_request('listMarketBook', {
                'marketIds': [market_id],
                'priceProjection': {
                    'priceData': ['EX_BEST_OFFERS']
                }
            })
            
            if market_book and market_book[0].get('runners'):
                race_data = convert_betfair_to_game_format(market, market_book[0], event_name)
                if race_data:
                    betfair_races.append(race_data)
    
    print(f"DEBUG: ✅ Retrieved {len(betfair_races)} Betfair races")
    return betfair_races

def convert_betfair_to_game_format(market, market_book, event_name):
    """Convert Betfair market data to game format"""
    try:
        race_id = f"betfair_{market.get('marketId', random.randint(1000, 9999))}"
        race_time = market.get('marketStartTime', datetime.now().isoformat())
        
        horses = []
        horse_odds = {}
        
        runners = market.get('runners', [])
        market_runners = market_book.get('runners', [])
        
        # Create lookup for odds by selection id
        odds_lookup = {}
        for runner in market_runners:
            selection_id = runner.get('selectionId')
            ex = runner.get('ex', {})
            available_to_back = ex.get('availableToBack', [])
            
            if available_to_back:
                # Use best back price (first in list)
                best_odds = available_to_back[0].get('price', 2.0)
                odds_lookup[selection_id] = float(best_odds)
        
        # Build race data
        for runner in runners:
            horse_name = runner.get('runnerName', f"Horse {len(horses)+1}")
            selection_id = runner.get('selectionId')
            
            horses.append(horse_name)
            
            # Get odds from market book, fallback to generated odds
            if selection_id in odds_lookup:
                odds = odds_lookup[selection_id]
            else:
                # Generate realistic odds if not available
                odds = round(random.uniform(2.0, 12.0), 2)
            
            horse_odds[horse_name] = odds
        
        # Ensure we have at least 5 horses
        while len(horses) < 5:
            horses.append(f"Mystery Horse {len(horses)+1}")
            horse_odds[horses[-1]] = round(random.uniform(4.0, 10.0), 2)
        
        return {
            'id': race_id,
            'horses': horses[:8],  # Max 8 horses
            'odds': horse_odds,
            'title': event_name,
            'start_time': race_time,
            'is_real_race': True,
            'data_source': 'Betfair Exchange API',
            'track': event_name.split(' ')[0] if event_name else 'Betfair Track',
            'race_number': 1
        }
        
    except Exception as e:
        print(f"Error converting Betfair race data: {e}")
        return None

def test_betfair_connection():
    """Test Betfair API connection"""
    try:
        if betfair_login():
            # Test getting event types
            event_types = betfair_api_request('listEventTypes', {})
            if event_types:
                return {
                    'status': 'success',
                    'message': f"✅ Connected to Betfair API - {len(event_types)} event types available",
                    'event_types': [et.get('eventType', {}).get('name') for et in event_types[:5]]
                }
            else:
                return {
                    'status': 'error',
                    'message': "❌ Connected but failed to get event types"
                }
        else:
            return {
                'status': 'error',
                'message': "❌ Failed to login to Betfair"
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"❌ Betfair connection error: {str(e)}"
        }
# ----- END BETFAIR EXCHANGE API FUNCTIONS -----

# ----- LOGIN REQUIRED DECORATOR -----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if user is admin
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            flash("Access denied. Admin privileges required.")
            return redirect(url_for('races'))
        
        return f(*args, **kwargs)
    return decorated_function
# ----- END LOGIN REQUIRED DECORATOR -----

# ----- TEMPLATE CONTEXT PROCESSOR -----
@app.context_processor
def inject_branding():
    """Inject branding variables into all templates"""
    context = {
        'app_name': APP_NAME,
        'app_tagline': APP_TAGLINE,
        'app_description': APP_DESCRIPTION,
        'currency_name': CURRENCY_NAME,
        'currency_symbol': CURRENCY_SYMBOL,
        'app_version': APP_VERSION,
        'app_author': APP_AUTHOR
    }
    
    # Add user coins if logged in
    if 'user_id' in session:
        context['user_coins'] = get_user_coins(session['user_id'])
    
    return context
# ----- END TEMPLATE CONTEXT PROCESSOR -----

@app.errorhandler(500)
def internal_error(error):
    tb = traceback.format_exc()
    print("=== Internal Server Error Traceback ===")
    print(tb)
    return "Internal Server Error - check server logs", 500

HORSE_COLORS = {
    "Thunderbolt": "#FFD700", "Lightning": "#ADD8E6", "Majestic": "#C0C0C0", "Shadowfax": "#A9A9A9",
    "Blaze": "#FF4500", "Golden Hoof": "#FFE066", "Silver Streak": "#B0C4DE", "Night Rider": "#483D8B",
    "Storm Runner": "#20B2AA", "Lucky Star": "#FF69B4",
    "Stormchaser": "#40E0D0", "Silverhoof": "#8C92AC", "Nightmare": "#000000", "Comet": "#FFDAB9",
    "Tornado": "#8A2BE2", "Fireball": "#FF6347", "Whirlwind": "#00CED1", "Mystic": "#9370DB",
    "Phantom": "#708090", "Eclipse": "#191970",
    "Red Rocket": "#FF0000", "Blue Moon": "#1E90FF", "Emerald Flash": "#50C878", "Desert Wind": "#EDC9AF",
    "Frostbite": "#B0E0E6", "Copperhead": "#B87333", "Violet Storm": "#8F00FF", "Shadow Dancer": "#36454F",
    "Wildfire": "#FF7F50", "Sunburst": "#FFD700",
    "Ironclad": "#43464B", "Blizzard": "#E0FFFF", "Celestial": "#6495ED", "Maple Leaf": "#D2691E",
    "Black Pearl": "#2E2E2E", "White Lightning": "#FFFFFF", "Crimson King": "#DC143C", "Aurora": "#7FFFD4",
    "Tempest": "#4682B4", "Galaxy": "#483D8B"
}

# ----- FORM, MOMENTUM, FAVOURITES, ODDS SYSTEM -----
horse_state = {}

def get_horse_state(horse):
    if horse not in horse_state:
        horse_state[horse] = {
            "momentum": 0,
            "consecutive_losses": 0,
            "total_races": 0
        }
    return horse_state[horse]

def reset_all_momentum():
    for h in horse_state:
        horse_state[h]['momentum'] = 0
        horse_state[h]['consecutive_losses'] = 0

from flask import session

def generate_race_form_and_odds(horses):
    form_dict = {}
    odds_dict = {}
    favourite_scores = {}
    
    # Load horse_state from session or initialize
    horse_state = session.get('horse_state', {})
    
    for horse in horses:
        form = random.randint(40, 100)
        # Get state from session-persisted horse_state
        state = horse_state.get(horse, {"momentum": 0, "consecutive_losses": 0, "total_races": 0})
        variance = random.randint(-10, 10)
        fav_score = form + state["momentum"] + variance
        form_dict[horse] = form
        favourite_scores[horse] = fav_score
    
    sorted_horses = sorted(horses, key=lambda h: favourite_scores[h], reverse=True)
    favourites = set(sorted_horses[:2])
    max_score = max(favourite_scores.values())
    min_score = min(favourite_scores.values())
    
    for horse in horses:
        if max_score == min_score:
            odds = 4.0
        else:
            odds = 8.0 - 6.2 * ((favourite_scores[horse] - min_score) / (max_score - min_score))
        odds = round(max(1.8, min(odds, 100.0)), 2)
        odds_dict[horse] = odds
    
    horse_infos = []
    for horse in horses:
        # Use momentum from session-persisted horse_state
        current_momentum = horse_state.get(horse, {}).get("momentum", 0)
        horse_infos.append({
            "name": horse,
            "form": form_dict[horse],
            "momentum": current_momentum,  # Now uses persisted momentum
            "odds": odds_dict[horse],
            "fractional_odds": decimal_to_nearest_fraction(odds_dict[horse]),
            "is_favourite": horse in favourites
        })
    
    return horse_infos, odds_dict


from flask import session

def update_horse_momentum(winner, horses):
    global horse_state
    # Load the current horse_state from session if available
    horse_state = session.get('horse_state', horse_state if 'horse_state' in globals() else {})
    for horse in horses:
        state = get_horse_state(horse)
        state["total_races"] += 1
        if horse == winner:
            state["momentum"] += 10
            state["consecutive_losses"] = 0
        else:
            state["momentum"] -= 15
            state["consecutive_losses"] += 1
            if state["consecutive_losses"] >= 2:
                state["momentum"] = 0
    # Save the updated horse_state to the session
    session['horse_state'] = horse_state


# Virtual races as fallback
virtual_races_list = [
    {
        "id": 1,
        "date": "2025-06-01",
        "horses": ["Thunderbolt", "Lightning", "Majestic", "Shadowfax", "Blaze", "Golden Hoof", "Silver Streak", "Night Rider", "Storm Runner", "Lucky Star"],
        "result": None,
        "is_real_race": False
    },
    {
        "id": 2,
        "date": "2025-06-02",
        "horses": ["Stormchaser", "Silverhoof", "Nightmare", "Comet", "Tornado", "Fireball", "Whirlwind", "Mystic", "Phantom", "Eclipse"],
        "result": None,
        "is_real_race": False
    },
    {
        "id": 3,
        "date": "2025-06-03",
        "horses": ["Red Rocket", "Blue Moon", "Emerald Flash", "Desert Wind", "Frostbite", "Copperhead", "Violet Storm", "Shadow Dancer", "Wildfire", "Sunburst"],
        "result": None,
        "is_real_race": False
    },
    {
        "id": 4,
        "date": "2025-06-04",
        "horses": ["Ironclad", "Blizzard", "Celestial", "Maple Leaf", "Black Pearl", "White Lightning", "Crimson King", "Aurora", "Tempest", "Galaxy"],
        "result": None,
        "is_real_race": False
    }
]

def get_races_list():
    """Get combined list of real and virtual races"""
    races = []
    
    # Try to get real races first (from Betfair if enabled)
    if USE_BETFAIR_API:
        try:
            print("DEBUG: Attempting to get real races from Betfair...")
            real_races = get_real_races()
            if real_races:
                print(f"Using {len(real_races)} real races from Betfair API")
                races.extend(real_races)
            else:
                print("No real races available from Betfair, using virtual races")
        except Exception as e:
            print(f"Error getting real races from Betfair: {e}")
    else:
        print("DEBUG: Betfair API disabled, using virtual races only")
    
    # Add virtual races if we don't have enough real ones
    if len(races) < 4:
        virtual_to_add = virtual_races_list[:4-len(races)]
        races.extend(virtual_to_add)
    
    return races

# Initialize with virtual races only to avoid startup API calls
races_list = virtual_races_list.copy()  # Don't call API on startup

def refresh_races_list():
    """Refresh the races list with new data"""
    global races_list
    races_list = get_races_list()
    return races_list

def ensure_race_winner_in_session(race_id, horses):
    if "race_winners" not in session:
        session["race_winners"] = {}
    winners = session["race_winners"]
    race_id_str = str(race_id)
    if race_id_str not in winners:
        horse_infos, odds_dict = generate_race_form_and_odds(horses)
        weights = []
        for h in horse_infos:
            weights.append(1.0 / h["odds"])
        winner_index = random.choices(range(len(horses)), weights=weights, k=1)[0]
        winners[race_id_str] = {
            "name": horses[winner_index],
            "index": winner_index
        }
        session["race_winners"] = winners
    return session["race_winners"][race_id_str]

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please fill in all fields.")
            return render_template("register.html")
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            conn.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken.")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/admin/api-config", methods=["GET", "POST"])
@admin_required
def api_config():
    """Admin page to configure API settings including Betfair"""
    global BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD, USE_BETFAIR_API, USE_VIRTUAL_RACING, RACING_MODE
    
    if request.method == "POST":
        # Betfair configuration
        betfair_app_key = request.form.get("betfair_app_key", "").strip()
        betfair_username = request.form.get("betfair_username", "").strip()
        betfair_password = request.form.get("betfair_password", "").strip()
        use_betfair = request.form.get("use_betfair") == "on"
        
        # Virtual racing configuration
        use_virtual = request.form.get("use_virtual") == "on"
        racing_mode = request.form.get("racing_mode", "enhanced")
        
        # Update global variables
        if betfair_app_key:
            BETFAIR_APP_KEY = betfair_app_key
        if betfair_username:
            BETFAIR_USERNAME = betfair_username
        if betfair_password:
            BETFAIR_PASSWORD = betfair_password
            
        USE_BETFAIR_API = use_betfair
        USE_VIRTUAL_RACING = use_virtual
        RACING_MODE = racing_mode
        
        # Save configuration
        save_api_config(
            use_virtual_racing=use_virtual,
            racing_mode=racing_mode,
            betfair_app_key=BETFAIR_APP_KEY,
            betfair_username=BETFAIR_USERNAME,
            betfair_password=BETFAIR_PASSWORD,
            use_betfair_api=use_betfair
        )
        
        flash("Configuration updated successfully!")
        flash(f"Betfair API {'enabled' if use_betfair else 'disabled'}")
        flash(f"Virtual racing {'enabled' if use_virtual else 'disabled'}")
        
        # Refresh races list with new settings
        refresh_races_list()
        
        return redirect(url_for('api_config'))
    
    # Test connections
    api_status = "Not configured"
    betfair_status = "Not configured"
    provider_info = ""
    
    # Test Betfair connection
    if USE_BETFAIR_API and BETFAIR_APP_KEY and BETFAIR_APP_KEY != "YOUR_BETFAIR_APP_KEY":
        test_result = test_betfair_connection()
        betfair_status = test_result['message']
        if test_result['status'] == 'success':
            provider_info = f"Betfair Exchange API - Real betting exchange data with live odds. Event types: {', '.join(test_result.get('event_types', [])[:3])}"
    
    # Test current system
    if USE_BETFAIR_API:
        api_status = betfair_status
    elif USE_VIRTUAL_RACING:
        try:
            if RACING_MODE == 'enhanced':
                virtual_events = fetch_enhanced_virtual_races()
            else:
                virtual_events = fetch_demo_race_data()
            
            if virtual_events:
                api_status = f"✅ Virtual Racing Active - {len(virtual_events)} {RACING_MODE} races generated"
                provider_info = f"{'Enhanced' if RACING_MODE == 'enhanced' else 'Demo'} Virtual Racing - No API dependencies, realistic UK racecourse simulation"
            else:
                api_status = "❌ Virtual racing generation failed"
                
        except Exception as e:
            api_status = f"❌ Virtual racing error: {str(e)}"
    else:
        api_status = "❌ No data source enabled"
    
    return render_template("admin_api_config.html", 
                         # Betfair settings
                         betfair_app_key=BETFAIR_APP_KEY if BETFAIR_APP_KEY != "YOUR_BETFAIR_APP_KEY" else "",
                         betfair_username=BETFAIR_USERNAME if BETFAIR_USERNAME != "YOUR_BETFAIR_USERNAME" else "",
                         betfair_password="[HIDDEN]" if BETFAIR_PASSWORD and BETFAIR_PASSWORD != "YOUR_BETFAIR_PASSWORD" else "",
                         use_betfair=USE_BETFAIR_API,
                         betfair_status=betfair_status,
                         # Virtual racing settings
                         use_virtual=USE_VIRTUAL_RACING,
                         racing_mode=RACING_MODE,
                         # Status info
                         api_status=api_status,
                         provider_info=provider_info)

@app.route("/admin/refresh-races")
@admin_required
def refresh_races_manual():
    """Manual route to refresh races data for testing"""
    global races_list
    try:
        print("Manually refreshing races data...")
        races_list = get_races_list()
        if any(race.get('is_real_race', False) for race in races_list):
            flash(f"✅ Refreshed! Found {len([r for r in races_list if r.get('is_real_race', False)])} real races")
        else:
            flash("🎮 No real races available, using virtual races")
        return redirect(url_for('races'))
    except Exception as e:
        flash(f"❌ Error refreshing races: {str(e)}")
        return redirect(url_for('races'))

@app.route("/admin/test-api")
@admin_required
def test_api_detailed():
    """Test Betfair API connection with detailed output"""
    if not USE_BETFAIR_API:
        return """
        <html>
        <head><title>API Test</title></head>
        <body style="font-family: monospace; margin: 20px; background: #f5f5f5;">
            <h2>🏇 API Test Results</h2>
            <div style="background: white; padding: 20px; border-radius: 8px;">
                ❌ Betfair API is not enabled<br>
                Please enable Betfair API in the configuration first.
            </div>
            <br>
            <a href="/admin/api-config" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">← Back to Config</a>
        </body>
        </html>
        """
    
    results = []
    
    # Test Betfair connection
    results.append("🏇 Betfair Exchange API Test")
    results.append(f"🔑 App Key: {BETFAIR_APP_KEY[:8]}...{BETFAIR_APP_KEY[-4:] if len(BETFAIR_APP_KEY) > 8 else '[SHORT]'}")
    results.append(f"👤 Username: {BETFAIR_USERNAME}")
    results.append(f"🌐 Login URL: {BETFAIR_LOGIN_URL}")
    results.append(f"📡 API URL: {BETFAIR_BASE_URL}")
    results.append("")
    
    # Test login
    results.append("🔐 Testing Betfair Login...")
    login_success = betfair_login()
    
    if login_success:
        results.append("✅ Login successful!")
        results.append(f"🎫 Session Token: {BETFAIR_SESSION_TOKEN[:16]}...{BETFAIR_SESSION_TOKEN[-8:] if BETFAIR_SESSION_TOKEN else '[NONE]'}")
        results.append("")
        
        # Test event types
        results.append("� Testing Event Types...")
        event_types = betfair_api_request('listEventTypes', {})
        
        if event_types:
            results.append(f"✅ Found {len(event_types)} event types")
            results.append("📊 Available sports:")
            for et in event_types[:10]:  # Show first 10
                name = et.get('eventType', {}).get('name', 'Unknown')
                results.append(f"   • {name}")
            results.append("")
            
            # Test horse racing specifically
            results.append("🏇 Testing Horse Racing Events...")
            try:
                horse_races = fetch_betfair_horse_racing_events()
                if horse_races:
                    results.append(f"✅ Found {len(horse_races)} horse racing events")
                    for race in horse_races[:3]:  # Show first 3
                        title = race.get('title', 'Unknown Race')
                        horse_count = len(race.get('horses', []))
                        results.append(f"   • {title} ({horse_count} runners)")
                else:
                    results.append("⚠️ No horse racing events found today")
            except Exception as e:
                results.append(f"❌ Error fetching horse races: {str(e)}")
                
        else:
            results.append("❌ Failed to get event types")
            
    else:
        results.append("❌ Login failed!")
        results.append("🔧 Possible issues:")
        results.append("   • Check your Betfair username and password")
        results.append("   • Verify your App Key is correct")
        results.append("   • Ensure your Betfair account is active")
        results.append("   • Check if you need to accept terms and conditions")
    
    results.append("")
    results.append("=" * 50)
    
    if login_success:
        results.append("🎉 SUCCESS! Betfair API is working")
        results.append("✅ Your account is properly configured")
    else:
        results.append("❌ API connection failed")
        results.append("🔧 Check your Betfair credentials and try again")
    
    # Format results as HTML
    html_results = "<br>".join(results)
    return f"""
    <html>
    <head><title>Betfair API Test Results</title></head>
    <body style="font-family: monospace; margin: 20px; background: #f5f5f5;">
        <h2>🏇 Betfair Exchange API Test</h2>
        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {html_results}
        </div>
        <br>
        <div style="text-align: center;">
            <a href="/admin/api-config" style="margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">← Back to API Config</a>
            <a href="/races" style="margin: 10px; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">View Races →</a>
            <a href="javascript:location.reload()" style="margin: 10px; padding: 10px 20px; background: #ffc107; color: black; text-decoration: none; border-radius: 5px;">🔄 Refresh Test</a>
        </div>
    </body>
    </html>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if session['login_attempts'] >= 5:
            flash("Too many failed login attempts. Please try again later.")
            return render_template("login.html")
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, password_hash, coins FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = username
            session["coins"] = user["coins"]
            session["bets"] = []
            session["multi_bets"] = []
            session["race_winners"] = {}
            session["multi_race_queue"] = []
            session['login_attempts'] = 0
            bonus_info = give_daily_bonus(user["id"])
            if bonus_info and bonus_info["bonus_given"]:
                session["daily_bonus"] = f"You received a daily bonus of {bonus_info['bonus']} coins! Streak: {bonus_info['login_streak']} days."
            else:
                session["daily_bonus"] = None
            return redirect(url_for("races"))
        else:
            session['login_attempts'] += 1
            flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT username, coins, wins, current_streak, longest_streak, highest_accumulator, total_bets, biggest_single_win, xp, rank, login_streak, id
        FROM users WHERE id = ?
    """, (user_id,))
    user = c.fetchone()
    conn.close()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))
    user_dict = dict(user)
    xp = user_dict.get("xp", 0)
    user_dict["number_rank"] = get_number_rank(xp)
    user_dict["rank_title"] = get_rank_title(user_dict["number_rank"])
    user_dict["acca_wins"] = count_acca_wins(user_id)
    unlocked_achievements = check_and_award_achievements(user_id, user_dict)
    achievements = get_unlocked_achievements(user_id)
    daily_bonus_msg = session.pop("daily_bonus", None)
    achievement_msg = None
    if unlocked_achievements:
        achievement_msg = " | ".join([f"Achievement Unlocked: {name} (+{reward} coins)" for name, reward in unlocked_achievements])
    return render_template('profile.html', user=user_dict, daily_bonus_msg=daily_bonus_msg, achievements=achievements, achievement_msg=achievement_msg)

@app.route("/", methods=["GET", "POST"])
def index():
    if 'user_id' in session:
        return redirect(url_for("races"))
    return redirect(url_for("login"))

@app.route("/races")
@login_required
def races():
    try:
        # Refresh races list to get latest real race data
        current_races = refresh_races_list()
        
        races_data = []
        race_states = {}
        for race in current_races:
            horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
            
            # Add real race indicator and additional info
            race_info = {
                "id": race["id"],
                "date": race.get("date", datetime.now().strftime("%Y-%m-%d")),
                "horses": horse_infos,
                "is_real_race": race.get("is_real_race", False),
                "title": race.get("title", f"Race {race['id']}")
            }
            
            # Add real race timing info if available
            if race.get("start_time"):
                race_info["start_time"] = race["start_time"]
            
            races_data.append(race_info)
            race_states[str(race["id"])] = {
                "horse_infos": horse_infos,
                "odds_dict": odds_dict
            }
        
        username = session.get("username")
        coins = get_user_coins(session["user_id"])
        session["coins"] = coins
        session["race_states"] = race_states  # Store all generated odds/info for this session
        
        return render_template("races.html", races=races_data, coins=coins, username=username)
    except Exception as e:
        print(">>> ERROR in /races route:", e)
        return f"Internal Server Error: {e}", 500


def get_user_coins(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row["coins"] if row else 0

@app.route("/place_bet/<int:race_id>", methods=["GET", "POST"])
@login_required
def place_bet(race_id):
    race = next((r for r in races_list if r["id"] == race_id), None)
    if not race:
        return "Race not found", 404

    # Use stored horse_infos and odds_dict from session for consistency
    race_states = session.get("race_states", {})
    race_state = race_states.get(str(race_id))
    if race_state:
        horse_infos = race_state["horse_infos"]
        odds_dict = race_state["odds_dict"]
    else:
        # fallback if not found (shouldn't happen if flow is correct)
        horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])

    error_message = None

    if request.method == "POST":
        # Process win bet
        horse = request.form.get("horse")
        try:
            amount = int(request.form.get("amount", 0))
        except ValueError:
            amount = 0

        # Process forecast bet
        forecast_first = request.form.get("forecast_first")
        forecast_second = request.form.get("forecast_second")
        try:
            forecast_amount = int(request.form.get("forecast_amount", 0))
        except ValueError:
            forecast_amount = 0

        # --- ENFORCE ONLY ONE BET TYPE ---
        win_bet_valid = horse and amount > 0
        forecast_bet_valid = (
            forecast_first and forecast_second
            and forecast_first != forecast_second
            and forecast_amount > 0
            and forecast_amount <= session.get("coins", 0)
        )

        if win_bet_valid and forecast_bet_valid:
            error_message = "Please place either a single bet OR a forecast bet, not both for the same race."
        elif win_bet_valid:
            if horse not in [h["name"] for h in horse_infos]:
                error_message = "Invalid horse choice"
            elif amount > session.get("coins", 0):
                error_message = "Not enough coins"
            else:
                session["coins"] -= amount
                update_user_coins(session["user_id"], session["coins"])
                bets = session.get("bets", [])
                bets.append({
                    "race_id": race_id,
                    "horse": horse,
                    "amount": amount,
                    "type": "win",
                    "odds": odds_dict[horse],
                    "fractional_odds": decimal_to_nearest_fraction(odds_dict[horse])
                })
                session["bets"] = bets
                update_user_stats(session["user_id"], won=False)
                return redirect(url_for("race_animation", race_id=race_id))
        elif forecast_bet_valid:
            session["coins"] -= forecast_amount
            update_user_coins(session["user_id"], session["coins"])
            bets = session.get("bets", [])
            bets.append({
                "race_id": race_id,
                "forecast_first": forecast_first,
                "forecast_second": forecast_second,
                "forecast_amount": forecast_amount,
                "type": "forecast"
            })
            session["bets"] = bets
            update_user_stats(session["user_id"], won=False)
            return redirect(url_for("race_animation", race_id=race_id))
        else:
            error_message = "No valid bet placed"

    return render_template(
        "place_bet.html",
        race={**race, "horses": horse_infos},
        coins=session.get("coins"),
        error_message=error_message
    )




# ------------------ MULTI-BET (ACCUMULATOR) ROUTE WITH DYNAMIC ODDS & MOMENTUM ------------------
@app.route("/multi_bet", methods=["GET", "POST"])
@login_required
def multi_bet():
    if request.method == "POST":
        selections = []
        accumulator_odds = 1.0
        accumulator_fractional = Fraction(1, 1)
        # Use the stored race states from the GET
        race_states = session.get("multi_bet_race_states", {})
        for race in races_list:
            horse = request.form.get(f"race_{race['id']}")
            if horse:
                race_state = race_states.get(str(race["id"]))
                if not race_state:
                    # fallback if not present
                    horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
                else:
                    horse_infos = race_state["horse_infos"]
                    odds_dict = race_state["odds_dict"]
                sel_odds = odds_dict[horse]
                accumulator_odds *= sel_odds
                accumulator_fractional *= Fraction.from_float(sel_odds - 1).limit_denominator(20)
                selections.append({"race_id": race["id"], "horse": horse, "odds": sel_odds})
        try:
            stake = int(request.form.get("multi_stake", 0))
        except ValueError:
            stake = 0
        if len(selections) < 2 or stake <= 0 or stake > session.get("coins", 0):
            return "Invalid multi-bet.", 400
        session["coins"] -= stake
        update_user_coins(session["user_id"], session["coins"])
        session["multi_bets"] = [{
            "selections": selections,
            "stake": stake,
            "accumulator_odds": round(accumulator_odds, 2),
            "accumulator_fractional": f"{accumulator_fractional.numerator}/{accumulator_fractional.denominator}"
        }]
        session["multi_race_progress"] = {
            "current_leg": 0,
            "results": [],
            "selections": selections,
            "stake": stake
        }
        # Store the race states for animation
        session["multi_race_states"] = race_states
        return redirect(url_for("multi_race_animation"))
    # GET: generate and store race states for display and POST
    races_data = []
    race_states = {}
    for race in races_list:
        horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
        races_data.append({"id": race["id"], "date": race["date"], "horses": horse_infos})
        race_states[str(race["id"])] = {
            "horse_infos": horse_infos,
            "odds_dict": odds_dict
        }
    session["multi_bet_race_states"] = race_states
    return render_template("multi_bet.html", races=races_data, coins=session.get("coins", 0))


@app.route("/multi_race_animation", methods=["GET", "POST"])
@login_required
def multi_race_animation():
    progress = session.get("multi_race_progress")
    if not progress:
        return redirect(url_for("results"))
    selections = progress["selections"]
    current_leg = progress["current_leg"]
    if current_leg >= len(selections):
        return redirect(url_for("results"))
    sel = selections[current_leg]
    race = next((r for r in races_list if r["id"] == sel["race_id"]), None)
    race_states = session.get("multi_race_states", {})
    race_state = race_states.get(str(race["id"]))
    if not race_state:
    # fallback for safety
        horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
    else:
        horse_infos = race_state["horse_infos"]
        odds_dict = race_state["odds_dict"]

    weights = [1.0 / h["odds"] for h in horse_infos]
    winner_index = random.choices(range(len(race["horses"])), weights=weights, k=1)[0]
    winner_name = race["horses"][winner_index]
    if len(progress["results"]) <= current_leg:
        progress["results"].append(winner_name)
    else:
        progress["results"][current_leg] = winner_name
    update_horse_momentum(winner_name, race["horses"])
    session["multi_race_progress"] = progress
    is_last = (current_leg == len(selections) - 1)
    race_for_template = dict(race)
    race_for_template["horses"] = horse_infos
    return render_template(
        "multi_race_animation.html",
        race=race_for_template,
        winner=winner_name,
        winner_index=winner_index,
        horse_colors=HORSE_COLORS,
        is_last=is_last
    )

@app.route("/multi_race_next", methods=["POST"])
@login_required
def multi_race_next():
    progress = session.get("multi_race_progress")
    if progress:
        progress["current_leg"] += 1
        session["multi_race_progress"] = progress
    return redirect(url_for("multi_race_animation"))

@app.route("/race_animation/<int:race_id>")
@login_required
def race_animation(race_id):
    race = next((r for r in races_list if r["id"] == race_id), None)
    if not race:
        return "Race not found", 404

    horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
    weights = [1.0 / h["odds"] for h in horse_infos]

    # Only generate and store the result if it doesn't already exist for this race
    race_results = session.setdefault("race_results", {})
    race_id_str = str(race_id)
    if race_id_str in race_results:
        # Use stored result
        winner_name = race_results[race_id_str]["winner"]
        finishing_order = race_results[race_id_str]["finishing_order"]
        winner_index = race["horses"].index(winner_name)
    else:
        # Generate new result and store it
        finishing_order = random.choices(race["horses"], weights=weights, k=len(race["horses"]))
        winner_name = finishing_order[0]
        winner_index = race["horses"].index(winner_name)
        race_results[race_id_str] = {
            "winner": winner_name,
            "finishing_order": finishing_order
        }
        session["race_results"] = race_results
        update_horse_momentum(winner_name, race["horses"])

    return render_template(
        "race_animation.html",
        race=race,
        horse_infos=horse_infos,
        winner=winner_name,
        winner_index=winner_index,
        horse_colors=HORSE_COLORS
    )


@app.route("/results")
@login_required
def results():
    bets = session.get("bets", [])
    multi_bets = session.get("multi_bets", [])
    user_id = session["user_id"]
    winnings = 0
    results_info = []

    # Process regular bets
    for bet in bets:
        race_id = bet["race_id"]
        bet_type = bet.get("type", "win")
        
        # Get race results from session
        race_results = session.get("race_results", {})
        race_result = race_results.get(str(race_id))
        
        if not race_result:
            continue
            
        winner = race_result["winner"]
        finishing_order = race_result.get("finishing_order", [])
        second = finishing_order[1] if len(finishing_order) > 1 else None

        if bet_type == "win":
            # Regular win bet
            amount = bet["amount"]
            horse = bet["horse"]
            odds = bet["odds"]
            won = (horse == winner)
            win_amount = int(amount * odds) if won else 0
            
            if won:
                update_user_stats(user_id, won=True, win_amount=win_amount)
            
            results_info.append({
                "race_id": race_id,
                "bet_type": "Win",
                "horse": horse,
                "amount": amount,
                "won": won,
                "win_amount": win_amount,
                "winner": winner,
                "odds": odds
            })
            winnings += win_amount
            
        elif bet_type == "forecast":
            # Forecast bet
            forecast_first = bet["forecast_first"]
            forecast_second = bet["forecast_second"]
            forecast_amount = bet["forecast_amount"]
            
            forecast_won = (winner == forecast_first and second == forecast_second)
            
            # Calculate forecast odds (simplified)
            race = next((r for r in races_list if r["id"] == race_id), None)
            if race:
                horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
                first_odds = odds_dict.get(forecast_first, 5.0)
                second_odds = odds_dict.get(forecast_second, 5.0)
                forecast_odds = first_odds * second_odds * 0.8
                forecast_win_amount = int(forecast_amount * forecast_odds) if forecast_won else 0
                
                if forecast_won:
                    update_user_stats(user_id, won=True, win_amount=forecast_win_amount)
                
                results_info.append({
                    "race_id": race_id,
                    "bet_type": "Forecast",
                    "forecast_first": forecast_first,
                    "forecast_second": forecast_second,
                    "amount": forecast_amount,
                    "won": forecast_won,
                    "win_amount": forecast_win_amount,
                    "winner": winner,
                    "second": second,
                    "odds": round(forecast_odds, 2)
                })
                winnings += forecast_win_amount

    # Process multi-bets (accumulators)
    for multi_bet in multi_bets:
        selections = multi_bet["selections"]
        stake = multi_bet["stake"]
        accumulator_odds = multi_bet["accumulator_odds"]
        
        # Check if all selections won
        all_won = True
        race_results = session.get("race_results", {})
        
        for selection in selections:
            race_id = selection["race_id"]
            horse = selection["horse"]
            race_result = race_results.get(str(race_id))
            
            if not race_result or race_result["winner"] != horse:
                all_won = False
                break
        
        win_amount = int(stake * accumulator_odds) if all_won else 0
        
        if all_won:
            update_user_stats(user_id, won=True, win_amount=win_amount, acca_win=win_amount)
        
        results_info.append({
            "bet_type": "Accumulator",
            "selections": selections,
            "stake": stake,
            "accumulator_odds": accumulator_odds,
            "won": all_won,
            "win_amount": win_amount
        })
        winnings += win_amount

    # Update user coins and achievements
    coins = get_user_coins(user_id) + winnings
    update_user_coins(user_id, coins)
    session["coins"] = coins

    # Check for achievements
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        unlocked_achievements = check_and_award_achievements(user_id, dict(user))
        if unlocked_achievements:
            for name, reward in unlocked_achievements:
                flash(f"Achievement Unlocked: {name} (+{reward} coins)")

    # Clear session data
    session["bets"] = []
    session["multi_bets"] = []
    session.pop("race_results", None)
    session.pop("multi_race_progress", None)

    return render_template("results.html", results=results_info, coins=coins)
    results_info = []
    user_id = session["user_id"]

    # Get stored race results from session
    race_results = session.get("race_results", {})

    # Process single bets (win and forecast)
    for bet in bets:
        race = next((r for r in races_list if r["id"] == bet.get("race_id")), None)
        if not race:
            continue

        # Use stored race result if available
        stored_result = race_results.get(str(race["id"]))
        if stored_result:
            winner = stored_result["winner"]
            finishing_order = stored_result["finishing_order"]
            second = finishing_order[1] if len(finishing_order) > 1 else None
        else:
            # Fallback (shouldn't happen if workflow is correct)
            horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])
            weights = [1.0 / h["odds"] for h in horse_infos]
            finishing_order = random.choices(race["horses"], weights=weights, k=len(race["horses"]))
            winner = finishing_order[0]
            second = finishing_order[1] if len(finishing_order) > 1 else None

        # Process WIN bets
        if bet.get("type") == "win":
            horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])  # Regenerate for current odds display
            won = winner == bet["horse"]
            odds = bet.get("odds", odds_dict.get(bet["horse"], 3.0))
            fractional_odds = bet.get("fractional_odds", decimal_to_nearest_fraction(odds))
            win_amount = int(bet["amount"] * odds) if won else 0
            is_favourite = next((h["is_favourite"] for h in horse_infos if h["name"] == bet["horse"]), False)
            results_info.append({
                "race_id": race["id"],
                "bet_type": "Win",
                "horse": bet["horse"],
                "amount": bet["amount"],
                "won": won,
                "win_amount": win_amount,
                "winner": winner,
                "odds": odds,
                "fractional_odds": fractional_odds,
                "is_favourite": is_favourite
            })
            winnings += win_amount

        # Process FORECAST bets
        elif bet.get("type") == "forecast":
            forecast_first = bet.get("forecast_first")
            forecast_second = bet.get("forecast_second")
            forecast_amount = bet.get("forecast_amount", 0)
            
            if forecast_first and forecast_second and forecast_amount > 0:
                forecast_won = (winner == forecast_first and second == forecast_second)
                horse_infos, odds_dict = generate_race_form_and_odds(race["horses"])  # Regenerate for current odds
                first_odds = odds_dict.get(forecast_first, 5.0)
                second_odds = odds_dict.get(forecast_second, 5.0)
                forecast_odds = first_odds * second_odds * 0.8
                forecast_win_amount = int(forecast_amount * forecast_odds) if forecast_won else 0
                results_info.append({
                    "race_id": race["id"],
                    "bet_type": "Forecast",
                    "forecast_first": forecast_first,
                    "forecast_second": forecast_second,
                    "amount": forecast_amount,
                    "won": forecast_won,
                    "win_amount": forecast_win_amount,
                    "winner": winner,
                    "second": second,
                    "odds": round(forecast_odds, 2)
                })
                winnings += forecast_win_amount

    # Process multi-bets (accumulators) - unchanged
    # ... [keep your existing multi-bet logic here] ...

    # Update coins and render results
    coins = get_user_coins(user_id) + winnings
    update_user_coins(user_id, coins)
    session["coins"] = coins

    # Clear stored race results after processing
    session.pop("race_results", None)

    response = render_template("results.html", results=results_info, coins=coins)
    session["bets"] = []
    session["multi_bets"] = []
    session["multi_race_progress"] = None
    return response




# ... [rest of your app.py unchanged] ...


@app.route("/leaderboard")
def leaderboard():
    sorted_leaderboard = load_leaderboard()
    return render_template("leaderboard.html", leaderboard=sorted_leaderboard)

if __name__ == "__main__":
    app.run(debug=True)

 
 #   A d d   c o n t e x t   p r o c e s s o r   f o r   b r a n d i n g 
 
 @ a p p . c o n t e x t _ p r o c e s s o r 
 
 d e f   i n j e c t _ b r a n d i n g ( ) : 
 
         r e t u r n   { 
 
                 ' a p p _ n a m e ' :   A P P _ N A M E , 
 
                 ' a p p _ t a g l i n e ' :   A P P _ T A G L I N E , 
 
                 ' a p p _ d e s c r i p t i o n ' :   A P P _ D E S C R I P T I O N , 
 
                 ' c u r r e n c y _ n a m e ' :   C U R R E N C Y _ N A M E , 
 
                 ' c u r r e n c y _ s y m b o l ' :   C U R R E N C Y _ S Y M B O L , 
 
                 ' a p p _ v e r s i o n ' :   A P P _ V E R S I O N , 
 
                 ' a p p _ a u t h o r ' :   A P P _ A U T H O R 
 
         } 
 
 