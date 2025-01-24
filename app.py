from flask import Flask, render_template, request, redirect, session, jsonify, url_for,flash
from flask_mail import Mail, Message
import psycopg2
import hashlib
import jwt
import datetime
import random
import string

app = Flask(__name__)
app.secret_key = 'my_secret_key'

DB_NAME = "postgres"
DB_USER = "postgres"
DB_HOST = 'localhost'
DB_PASSWORD = "1234"
PORT = 5432

def create_users_table():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_users_table()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/registerpage')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        email = request.form['email']
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO book (username, password,email) VALUES (%s, %s, %s)', (username, password,email))
            conn.commit()
            return '<script>alert("Register succesfull"); window.location.href="/loginpage";</script>'
        except psycopg2.IntegrityError:
            conn.rollback()
            return '<script>alert("Username or email already exists!"); window.location.href="/loginpage";</script>'
        finally:
            conn.close()
    else:
        return '<script>alert("Error"); window.location.href="/loginpage";</script>'

@app.route("/loginpage")
def loginpage():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        provided_password = hash_password(request.form['password']) 
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM book WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[2] == provided_password:  
            session['username'] = username
            # Generate a random string
            random_string = generate_random_string(10)  # Change the length as needed
            return redirect(url_for('profile_with_string', string_value=random_string))
        else:
             return '<script>alert("Invalid username or password"); window.location.href="/loginpage";</script>'
        
    else:
        return redirect('/')

@app.route('/profile/<string:string_value>')
def profile_with_string(string_value):
    if 'username' in session:
        username = session['username']
        # Check if the provided string matches the expected format
        if string_value.isalnum():
            return render_template('welcome.html', username=username, string_value=string_value)
        else:
            return '<script>alert("Invalid URL!"); window.location.href="/loginpage";</script>'
    else:
        return redirect('/loginpage')

@app.route("/contactpage")
def contactpage():
    return render_template('contact.html')

@app.route('/logout')
def logout():
    return '<script>alert("Logout successfull"); window.location.href="/loginpage";</script>'
    


@app.route('/protected')
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return jsonify({'message': f'Welcome {payload["username"]}! This is a protected resource.'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    



    
if __name__ == '__main__':
    app.run(debug=True,port=5000)
