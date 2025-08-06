# RaceCoin - Virtual Horse Racing & Betting

![RaceCoin Logo](https://img.shields.io/badge/RaceCoin-Virtual%20Horse%20Racing-yellow?style=for-the-badge)

##  About RaceCoin

RaceCoin is an immersive virtual horse racing and betting platform that brings the excitement of the track to your browser. Experience realistic racing action, place strategic bets, and climb the leaderboards in this comprehensive gaming experience.

##  Key Features

- ** Virtual Racing**: Enhanced virtual horse racing with realistic odds and outcomes
- ** RaceCoin Economy**: Earn and spend RaceCoins with a comprehensive achievement system
- ** Achievement System**: Unlock badges and earn rewards for various milestones
- ** Leaderboards**: Compete with other players for the top spot
- ** User Profiles**: Track your progress, stats, and achievements
- ** Responsive Design**: Play on any device with our mobile-friendly interface

##  Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Templating**: Jinja2
- **Authentication**: Secure session management
- **Deployment**: Railway (Production), Gunicorn (WSGI Server)

##  Installation & Setup

### Local Development

1. Clone the repository:
`ash
git clone https://github.com/yourusername/racecoin.git
cd racecoin
`

2. Create virtual environment:
`ash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
`

3. Install dependencies:
`ash
pip install -r requirements.txt
`

4. Run the application:
`ash
python app.py
`

5. Open your browser to http://localhost:5000

### Production Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Set environment variables:
   - FLASK_ENV=production
   - SECRET_KEY=your-secret-key
3. Deploy automatically on push to main branch

##  How to Play

1. **Register**: Create your RaceCoin account
2. **Explore Races**: Browse available virtual horse races
3. **Place Bets**: Use your RaceCoins to bet on horses
4. **Watch Races**: Experience live race animations
5. **Collect Winnings**: Successful bets earn you more RaceCoins
6. **Unlock Achievements**: Complete challenges to earn badges and bonuses
7. **Climb Leaderboards**: Compete with other players

##  Achievement System

- **First Bet**: Place your first bet (200 RC reward)
- **First Win**: Win your first race (300 RC reward)  
- **Streak Master**: Build login streaks (300-4000 RC rewards)
- **High Roller**: Win big amounts (2000+ RC rewards)
- **Level Achievements**: Reach various XP levels (1000-25000 RC rewards)

##  Game Features

- **Real-time Racing**: Watch horses compete in live animations
- **Dynamic Odds**: Realistic betting odds that change based on conditions
- **Multi-bet Support**: Place accumulator bets for bigger rewards
- **Daily Bonuses**: Login daily for bonus RaceCoins
- **XP System**: Level up by winning races and completing achievements

##  Security Features

- Secure password hashing (Werkzeug)
- Session-based authentication
- CSRF protection
- SQL injection prevention
- Environment-based configuration

##  Future Enhancements

- [ ] Multiplayer tournaments
- [ ] Social features (friends, messaging)
- [ ] Mobile app development
- [ ] Additional betting types
- [ ] Real racing data integration
- [ ] Cryptocurrency integration

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Contact

For support or questions, please open an issue on GitHub.

---

**Enjoy the thrill of virtual horse racing with RaceCoin!** 
