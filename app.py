from flask import Flask, render_template,request, Blueprint, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import random
from datetime import datetime

admin_r = Blueprint('admin',__name__, url_prefix='/admin')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rubbish.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'WoCAoNIMaLeGEB6666'

#initialise database and admin blueprint
db = SQLAlchemy()
db.init_app(app)
app.register_blueprint(admin_r)

login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))
    role = db.Column(db.String(10))
    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False

class News(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    question = db.Column(db.Text)
    option_A = db.Column(db.Text)
    option_B = db.Column(db.Text)
    option_C = db.Column(db.Text)
    answer = db.Column(db.Text)
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    number_of_question_attempted = db.Column(db.Integer)
    number_of_question_correct = db.Column(db.Integer)
    date = db.Column(db.DateTime)    


@login_manager .user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/")
def homepage():
    return render_template('homepage.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or "/")
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        if password != password2:
            message = "Passwords entered are not identical"
            return render_template('signup.html', message=message)
        entry = User(
            username = username,
            password = password
        )
        db.session.add(entry)
        db.session.commit()
        return redirect("/login")

    else:
        return render_template('signup.html')

@app.route("/forgetpassword")
def forgetpassword():
    return render_template('forgetpassword.html')

@app.route("/admin/create_news", methods=['GET', 'POST'])
@login_required
def create_news_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash('Title and content are required!', 'danger')
            return render_template('create_news_article.html')

        new_article = News(title=title, content=content)
        db.session.add(new_article)
        db.session.commit()
        flash('News article created successfully!', 'success')
        return redirect(url_for('news_list'))
        
    return render_template('create_news_article.html')

@app.route("/news")
def news_list():
    articles = News.query.order_by(News.date.desc()).all()
    return render_template('news_list.html', articles=articles)

@app.route("/news/<int:news_id>")
def news_detail(news_id):
    article = News.query.get_or_404(news_id)
    return render_template('news_detail.html', article=article)



@app.route("/create_quiz_number_of_questions")
@login_required
def create_quiz_number_of_questions():
    return render_template('quiz_number_of_questions.html')

@app.route("/create_quiz", methods=['GET','POST'])
@login_required
def create_quiz():
    if request.method == 'GET':
        number_of_question = request.args.get('number_of_questions')
        if number_of_question:
            number = int(number_of_question)
            return render_template('create_quiz.html', number=number)
        else:
            return redirect("/create_quiz_number_of_questions")
    elif request.method == 'POST':
        number_of_question = int(request.args.get('number_of_questions'))
        for i in range(number_of_question):
            question =  request.form[str(i)]
            option_A = request.form["A" + str(i)]
            option_B = request.form["B" + str(i)]
            option_C = request.form["C" + str(i)]
            answer = request.form["Answer" + str(i)]
            entry = Quiz(
                question = question,
                option_A = option_A,
                option_B = option_B,
                option_C = option_C,
                answer = answer
            )
            db.session.add(entry)
        db.session.commit()
        return redirect("/")


@app.route("/quiz", methods=['GET', 'POST'])
@login_required
def quiz():
    QUIZ_SIZE = 10
    
    if request.method == 'POST':
        score = 0
        user_answers = {}
        correct_answers = {}
        question_ids = list(request.form.keys())
        questions = Quiz.query.filter(Quiz.id.in_(question_ids)).all()
        
        for q in questions:
            user_choice = request.form.get(str(q.id))
            user_answers[q.id] = user_choice
            
            correct_answers[q.id] = q.answer
            
            if user_choice == q.answer:
                score += 1
                
        flash(f"You scored {score}/{len(questions)}!", "info")
        
        return render_template('quiz.html', questions=questions, user_answers=user_answers, correct_answers=correct_answers, show_results=True)
    
    else:
        all_questions = Quiz.query.all()
        if len(all_questions) < QUIZ_SIZE:
            flash(f"There are not enough questions in the database to create a {QUIZ_SIZE}-question quiz.", "danger")
            return redirect(url_for('homepage'))
        
        questions = random.sample(all_questions, QUIZ_SIZE)
        
        return render_template('quiz.html', questions=questions, show_results=False)
    


if __name__ == '__main__':
      with app.app_context():
          db.create_all()
      app.run(host='127.0.0.1', port=8000)