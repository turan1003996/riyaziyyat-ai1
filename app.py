from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user

# 1. Tətbiqi yaradırıq
app = Flask(__name__)
app.config['SECRET_KEY'] = 'K9#mP$1!xL892@qz373FFDF'

# DATETIME-I ŞABLONLARA TANITMAQ ('datetime is undefined' xətasını həll edir)
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

# -------------------------------------------------------------
# FLASK-LOGIN SAZLANMASI
# -------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# -------------------------------------------------------------
# MARŞRUTLAR (ROUTES)
# -------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/olympiad')
def olympiad():
    return render_template('olympiad.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

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
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Cavab/Rəy yazmaq üçün daxil olmalısınız!", "warning")
            return redirect(url_for('login'))

        content = request.form.get('content', '').strip()

    return f"Sual ID: {q_id}"

# -------------------------------------------------------------
# LOKALDA TƏTBİQİ İŞƏ SALAN HİSSƏ
# -------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)