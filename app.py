#! /usr/bin/python3

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
import os
from werkzeug import generate_password_hash
from werkzeug import check_password_hash
from flaskext.mysql import MySQL
from dbconfig.config import db


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(10)
app.config['MYSQL_DATABASE_HOST'] = db['host']
app.config['MYSQL_DATABASE_USER'] = db['user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['password']
app.config['MYSQL_DATABASE_DB'] = db['name']

# Initialize database variables..
mysql = MySQL()
mysql.init_app(app)

conn = mysql.connect()
cur = conn.cursor()

# Initialize flask-login..
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = ''


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


class User(UserMixin):
    def __init__(self, username):
        self.id = username

    # def get_id(self):
    #     return (self.user_id)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/signin')
@app.route('/login')
def login():
    return render_template('login.html',
                           title='Log In')


@app.route('/signup')
@app.route('/join', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    # [Do] Process data instead..
    name = request.form['name']
    username = request.form['username']
    email = request.form['email']
    passwd = request.form['passwd']

    # [Later] Check for sanity of fields, redirect if unclean (avoid SQLIA).

    # [Do] Check for username availability (assuming clean data)
    q = "SELECT user_id FROM `credentials` WHERE username='{}';"
    q.format(username)
    cur.execute(q)
    match = cur.fetchone()

    if not match is None:
        return render_template('signup.html',
                               issue='Username already taken')

    # Proceed with insertion otherwise.
    q = '''
    INSERT INTO `credentials` (username, name, hash, email) 
    VALUES (%s,%s,%s,%s)
    '''

    try:
        cur.execute(q, (username,
                        name,
                        generate_password_hash(passwd, method='sha1'),
                        email))
        conn.commit()

    except Exception as e:
        error = '''
        Something bad happened :(
        <h3>Click <a href="{{ url_for('index') }}">here</a> to return to home page.</h3>
        Error Description: {}
        '''.format(e)

        return error

    # Log the user in.
    login_user(User(username))
    return redirect(url_for('dashboard', username=username))



# PROTECTED ROUTES


@app.route('/<string:username>')
@login_required
def dashboard(username):
    return render_template('dashboard.html', username=username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # In dev mode:
    app.run(debug=True)
