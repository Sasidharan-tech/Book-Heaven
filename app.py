from flask import Flask, render_template, request, redirect, session, jsonify, Response
import psycopg2
import hashlib
import jwt
import datetime

app = Flask(__name__)
app.secret_key = 'my_secret_key'


DB_NAME = "postgres"
DB_USER = "postgres" 
DB_HOST= 'localhost'
DB_PASSWORD = "sasi"
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
        CREATE TABLE IF NOT EXISTS new_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL
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

@app.route('/')
def index_page():
    return render_template('index.html')

# @app.route('index')


@app.route('/registerpage')
def register_page():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])  # Hash  password
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO new_users (username, password) VALUES (%s, %s)', (username, password))
            conn.commit()
            return redirect('/loginpage')
        except psycopg2.IntegrityError:
            conn.rollback()
            return '<h1>Username already exists!</h1>'
        finally:
            conn.close()
    else:
         return redirect('/loginpage')
        





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
        cursor.execute('SELECT * FROM new_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[2] == provided_password:  
            session['username'] = username
            token = generate_token(username)
            return redirect('/profile')
        else:
            return '<h1>Invalid username or password!</h1>'
    else:
        return redirect('/')



@app.route('/profile')
def profile():
    # if 'username' in session:
    #     return f'<h1>Welcome, {session["username"]}!</h1>'
    # else:
    #     return redirect('/')
    return render_template('welcome.html')
    
    
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
