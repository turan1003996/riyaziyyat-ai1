import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 1. Tətbiqi yaradırıq
app = Flask(__name__)
app.config['SECRET_KEY'] = 'K9#mP$1!xL892@qz373FFDF'

# Məlumat bazası sazlanması (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DATETIME-I ŞABLONLARA TANITMAQ
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

# -------------------------------------------------------------
# MƏLUMAT BAZASI MODELLƏRİ
# -------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    points = db.Column(db.Integer, default=0)
    questions = db.relationship('Question', backref='author', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_primary_key=False, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    q_type = db.Column(db.String(50), default='Müzakirə') # 'Olimpiada Sualı' və s.
    category = db.Column(db.String(50), default='Ümumi')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Məlumat bazasını avtomatik yaratmaq
with app.app_context():
    db.create_all()

# -------------------------------------------------------------
# FLASK-LOGIN SAZLANMASI
# -------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------------------
# MARŞRUTLAR (ROUTES)
# -------------------------------------------------------------
@app.route('/')
def home():
    # index.html tərəfindən gözlənilən dinamik məlumatlar
    total_users = User.query.count()
    total_q = Question.query.count()
    questions = Question.query.order_by(Question.created_at.desc()).limit(10).all()
    top_users = User.query.order_by(User.points.desc()).limit(5).all()

    return render_template(
        'index.html',
        total_users=total_users,
        total_q=total_q,
        questions=questions,
        top_users=top_users
    )

@app.route('/olympiad')
def olympiad():
    return render_template('olympiad.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

# GİRİŞ HİSSƏSİ (LOGIN)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        login_input = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter((User.username == login_input) | (User.email == login_input)).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Müvəffəqiyyətlə daxil oldunuz!', 'success')
            return redirect(url_for('home'))
        else:
            flash('İstifadəçi adı/E-poçt və ya şifrə yanlışdır!', 'danger')

    return render_template('login.html')

# QEYDİYYAT HİSSƏSİ (REGISTER)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_by_email = User.query.filter_by(email=email).first()
        user_by_name = User.query.filter_by(username=username).first()

        if user_by_email:
            flash('Bu e-poçt ünvanı artıq qeydiyyatdan keçib!', 'warning')
            return redirect(url_for('register'))

        if user_by_name:
            flash('Bu istifadəçi adı artıq götürülüb!', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        
        new_user = User(username=username, email=email, password=hashed_password, points=0)
        db.session.add(new_user)
        db.session.commit()

        flash('Qeydiyyat uğurla tamamlandı! İndi daxil ola bilərsiniz.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ÇIXIŞ HİSSƏSİ (LOGOUT)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Hesabdan çıxış edildi.', 'info')
    return redirect(url_for('home'))

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    return render_template('reset_password.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    return render_template('feedback.html')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template('admin.html')

@app.route('/question/<int:q_id>', methods=['GET', 'POST'])
def question_detail(q_id):
    question = Question.query.get_or_404(q_id)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Cavab/Rəy yazmaq üçün daxil olmalısınız!", "warning")
            return redirect(url_for('login'))

        content = request.form.get('content', '').strip()

    return render_template('question_detail.html', question=question)

# -------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)