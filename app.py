from flask import Flask, request, render_template, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1 = db.Column(db.String(100), nullable=False)
    player2 = db.Column(db.String(100), nullable=False)
    character1 = db.Column(db.String(100), nullable=False)
    character2 = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    theme = request.args.get('theme')

    if theme:
        response = redirect(url_for('home'))
        response.set_cookie('theme_color', theme, max_age=60 * 60 * 24 * 30)
        return response

    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))

        return 'Invalid username or password'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existingUser = User.query.filter_by(username=username).first()

        if existingUser:
            return 'Username already exists'

        newUser = User(username=username, password=password)

        db.session.add(newUser)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    matches = match.query.filter_by(userID=user_id).all()
    total = len(matches)

    one_week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_matches = match.query.filter(
        match.userID == user_id,
        match.date >= one_week_ago
    ).all()

    weekly_count = len(weekly_matches)

    win_matches = match.query.filter(
        match.userID == user_id,
        match.result == 'Win'
    ).all()

    percentage = len(win_matches) * 100 / total if total > 0 else 0

    characters = [m.character1 for m in matches]
    counter = Counter(characters)

    if counter:
        most_character, count = counter.most_common(1)[0]
    else:
        most_character = 'No data'
        count = 0

    return render_template(
        'dashboard.html',
        total=total,
        weekly_count=weekly_count,
        percentage=percentage,
        most_character=most_character,
        count=count
    )

@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        player1 = request.form['player1']
        player2 = request.form['player2']
        character1 = request.form['character1']
        character2 = request.form['character2']
        result = request.form['result']

        newMatch = match(
            player1=player1,
            player2=player2,
            character1=character1,
            character2=character2,
            result=result,
            userID=session['user_id']
        )

        db.session.add(newMatch)
        db.session.commit()

        return redirect(url_for('add_match'))

    return render_template('add_match.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    query = match.query.filter_by(userID=session['user_id'])
    result = request.args.get('result')
    character = request.args.get('character')
    opponent = request.args.get('opponent')
    sort = request.args.get('sort')
    if result:
        query = query.filter(match.result == result)
    if character:
        query = query.filter(match.character1.ilike(f"%{character}%"))
    if opponent:
        query = query.filter(match.player2.ilike(f"%{opponent}%"))
    if sort == 'old':
        query = query.order_by(match.date.asc())
    else:
        query = query.order_by(match.date.desc())
    matches = query.all()
    return render_template('history.html', matches=matches)

@app.route('/edit_match/<int:match_id>', methods=['GET', 'POST'])
def edit_match(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur_match = match.query.filter_by(id=match_id).first()

    if cur_match is None:
        return 'Match not found'

    if request.method == 'POST':
        cur_match.player1 = request.form['player1']
        cur_match.player2 = request.form['player2']
        cur_match.character1 = request.form['character1']
        cur_match.character2 = request.form['character2']
        cur_match.result = request.form['result']

        db.session.commit()

        return redirect(url_for('history'))

    return render_template('edit_match.html', match=cur_match)

@app.route('/delete_match/<int:match_id>')
def delete_match(match_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur_match = match.query.filter_by(
        id=match_id,
        userID=session['user_id']
    ).first()

    if cur_match:
        db.session.delete(cur_match)
        db.session.commit()

    return redirect(url_for('history'))
@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    matches = match.query.filter_by(userID=session['user_id']).order_by(match.date.desc()).all()

    current_streak = 0
    streak_type = 'Win'
    best_character = 'No data'
    best_character_rate = 0
    most_opponent = 'No data'
    opponent_count = 0
    last5_wins = 0
    strongest_matchup = 'No data'
    strongest_rate = 0
    hardest_matchup = 'No data'
    hardest_rate = 0
    character_stats = []

    if matches:
        streak_type = matches[0].result

        for m in matches:
            if m.result == streak_type:
                current_streak += 1
            else:
                break

        last5 = matches[:5]
        last5_wins = sum(1 for m in last5 if m.result == 'Win')

        opponent_counter = Counter(m.player2 for m in matches)
        most_opponent, opponent_count = opponent_counter.most_common(1)[0]

        char_data = {}

        for m in matches:
            char = m.character1

            if char not in char_data:
                char_data[char] = {
                    'matches': 0,
                    'wins': 0,
                    'losses': 0
                }

            char_data[char]['matches'] += 1

            if m.result == 'Win':
                char_data[char]['wins'] += 1
            else:
                char_data[char]['losses'] += 1

        for char in char_data:
            data = char_data[char]
            win_rate = round(data['wins'] * 100 / data['matches'])

            character_stats.append({
                'name': char,
                'matches': data['matches'],
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate
            })

        best_character_rate = -1

        for char in character_stats:
            if char['win_rate'] > best_character_rate:
                best_character_rate = char['win_rate']
                best_character = char['name']

        matchup_data = {}

        for m in matches:
            opponent_char = m.character2

            if opponent_char not in matchup_data:
                matchup_data[opponent_char] = {
                    'wins': 0,
                    'matches': 0
                }

            matchup_data[opponent_char]['matches'] += 1

            if m.result == 'Win':
                matchup_data[opponent_char]['wins'] += 1

        strongest_rate = -1
        hardest_rate = 101

        for opponent_char in matchup_data:
            data = matchup_data[opponent_char]
            rate = round(data['wins'] * 100 / data['matches'])

            if rate > strongest_rate:
                strongest_rate = rate
                strongest_matchup = opponent_char

            if rate < hardest_rate:
                hardest_rate = rate
                hardest_matchup = opponent_char

    return render_template(
        'analytics.html',
        current_streak=current_streak,
        streak_type=streak_type,
        best_character=best_character,
        best_character_rate=best_character_rate,
        most_opponent=most_opponent,
        opponent_count=opponent_count,
        last5_wins=last5_wins,
        strongest_matchup=strongest_matchup,
        strongest_rate=strongest_rate,
        hardest_matchup=hardest_matchup,
        hardest_rate=hardest_rate,
        character_stats=character_stats
    )

if __name__ == '__main__':
    app.run(debug=True)
