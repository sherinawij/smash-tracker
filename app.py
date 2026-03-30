from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

@app.route('/')
def home():
    return render_template('home.html')
    # return "Hello, Smash App!"

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existingUser = User.query.filter_by(username=username).first()
        if existingUser:
            return "Username already exists"
        hashPassword = generate_password_hash(password)
        newUser = User(username=username, password=hashPassword)
        db.session.add(newUser)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')
    
class match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1 = db.Column(db.String(100), nullable=False)
    player2 = db.Column(db.String(100), nullable=False)
    character1 = db.Column(db.String(100), nullable=False)
    character2 = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    if request.method == 'POST':
        player1 = request.form['player1']
        player2 = request.form['player2']
        character1 = request.form['character1']
        character2 = request.form['character2']
        result = request.form['result']
        newMatch = match(player1=player1, player2=player2, character1=character1, character2=character2, result=result, userID=current_user.id)
        db.session.add(newMatch)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        return render_template('add_match.html')
    
@app.route('/history', methods=['GET'])
def history(): 
    matches = match.query.filter_by(userID=current_user.id).all()
    return render_template('history.html', matches=matches)

if __name__ == '__main__':
    app.run(debug=True)