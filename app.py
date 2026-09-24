import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ================= 1. FLASK VƏ TƏHLÜKƏSİZLİK TƏYİNATI =================
app = Flask(__name__)

# Bot və Brute-Force hücumlarından qorunmaq üçün Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

# ================= 2. KONFİQURASİYALAR =================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'math-olympiad-secure-key-2026-xyz')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_DIR, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ADMIN_EMAIL'] = 'admin@matholympiad.az'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_now():
    return {'datetime': datetime, 'admin_email': app.config['ADMIN_EMAIL']}

# ================= 3. VERİLƏNLƏR BAZASI MODELLƏRİ =================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

comment_likes = db.Table('comment_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('comment_id', db.Integer, db.ForeignKey('comment.id'))
)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    q_type = db.Column(db.String(50), default="Olimpiada Sualı")
    category = db.Column(db.String(50), default="Cəbr")
    content = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship('Comment', backref='question', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(255), nullable=True)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    likes = db.relationship('User', secondary=comment_likes, backref=db.backref('liked_comments', lazy='dynamic'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= 4. MARŞRUTLAR (ROUTES) =================

@app.route('/')
def home():
    questions = Question.query.order_by(Question.created_at.desc()).limit(6).all()
    top_users = User.query.order_by(User.points.desc()).limit(5).all()
    total_q = Question.query.count()
    total_users = User.query.count()
    return render_template('index.html', questions=questions, top_users=top_users, total_q=total_q, total_users=total_users)

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        flash("Təklif və ya rəyiniz uğurla adminə göndərildi! Təşəkkür edirik.", "success")
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

@app.route('/olympiad', methods=['GET', 'POST'])
def olympiad():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Sual və ya mövzu paylaşmaq üçün giriş etməlisiniz!", "warning")
            return redirect(url_for('login'))

        title = request.form.get('title', '').strip()
        q_type = request.form.get('q_type', 'Olimpiada Sualı')
        category = request.form.get('category', 'Cəbr')
        content = request.form.get('content', '').strip()
        image_file = request.files.get('image')

        filename = None
        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            filename = secure_filename(f"q_{current_user.id}_{int(datetime.now().timestamp())}_{image_file.filename}")
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if title and (content or filename):
            new_q = Question(
                user_id=current_user.id,
                title=title,
                q_type=q_type,
                category=category,
                content=content,
                image_file=filename
            )
            current_user.points += 10
            db.session.add(new_q)
            db.session.commit()
            flash("Paylaşım uğurla əlavə olundu! (+10 Xal)", "success")
            return redirect(url_for('olympiad'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('olympiad.html', questions=questions)

@app.route('/question/<int:q_id>', methods=['GET', 'POST'])
def question_detail(q_id):
    question = Question.query.get_or_404(q_id)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Cavab/Rəy yazmaq üçün daxil olmalısınız!", "warning")
            return redirect(url_for('login'))

        content = request.form.get('content', '').strip()
        image_file = request.files.get('image')

        filename = None
        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            filename = secure_filename(f"c_{current_user.id}_{int(datetime.now().timestamp())}_{image_file.filename}")
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if content or filename:
            comment = Comment(
                question_id=question.id,
                user_id=current_user.id,
                content=content,
                image_file=filename
            )
            current_user.points += 5
            db.session.add(comment)
            db.session.commit()
            flash("Rəyiniz əlavə edildi! (+5 Xal)", "success")
            return redirect(url_for('question_detail', q_id=q_id))

    comments = Comment.query.filter_by(question_id=question.id).order_by(Comment.is_pinned.desc(), Comment.created_at.asc()).all()
    return render_template('question_detail.html', question=question, comments=comments)

@app.route('/pin_comment/<int:c_id>')
@login_required
def pin_comment(c_id):
    comment = Comment.query.get_or_404(c_id)
    question = Question.query.get(comment.question_id)

    if question.user_id != current_user.id:
        flash("Yalnız sual sahibi rəyi pin edə bilər!", "danger")
        return redirect(url_for('question_detail', q_id=question.id))

    comment.is_pinned = not comment.is_pinned
    db.session.commit()
    flash("Pin statusu dəyişdirildi!", "info")
    return redirect(url_for('question_detail', q_id=question.id))

@app.route('/like_comment/<int:c_id>')
@login_required
def like_comment(c_id):
    comment = Comment.query.get_or_404(c_id)
    if current_user in comment.likes:
        comment.likes.remove(current_user)
    else:
        comment.likes.append(current_user)
    db.session.commit()
    return redirect(url_for('question_detail', q_id=comment.question_id))

@app.route('/leaderboard')
def leaderboard():
    top_users = User.query.order_by(User.points.desc()).all()
    return render_template('leaderboard.html', top_users=top_users)

# Giriş Səhifəsi - 1 dəqiqədə maksimum 5 cəhd
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        login_input = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter(
            (User.username.ilike(login_input)) | (User.email.ilike(login_input))
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Uğurla giriş etdiniz!", "success")
            return redirect(url_for('home'))

        flash("İstifadəçi adı/Email və ya şifrə yanlışdır!", "danger")
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            flash("Şifrənizi sıfırlamaq üçün təlimatlar e-poçt ünvanınıza göndərildi!", "info")
            return redirect(url_for('login'))
        else:
            flash("Bu e-poçt ünvanı ilə qeydiyyatdan keçmiş istifadəçi tapılmadı.", "warning")

    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if User.query.filter_by(username=username).first():
            flash("İstifadəçi adı artıq mövcuddur!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Bu e-poçt ünvanı artıq qeydiyyatdan keçib!", "danger")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Qeydiyyat tamamlandı! İndi daxil ola bilərsiniz.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Hesabdan çıxıldı.", "info")
    return redirect(url_for('home'))

# ================= 5. TƏTBİQİ BAŞLATMAQ =================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # CANLI SERVERDƏ MÜTLƏQ debug=False OLMALIDIR
    app.run(debug=False)