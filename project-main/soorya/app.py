
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_mail import Mail, Message
import re
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Soorya@0213",
    database="faculty"
)
cursor = db.cursor()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sooryas851@gmail.com'
app.config['MAIL_PASSWORD'] = 'jznu akjd vlrf iwkr'

mail = Mail(app)

# Login required decorator
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    return render_template('new.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=session.get('username'), user_type=session.get('user_type'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']

    select_query = "SELECT * FROM users WHERE username = %s AND password = %s AND user_type = %s"
    cursor.execute(select_query, (username, password, user_type))
    user = cursor.fetchone()

    if user:
        session['username'] = username
        session['user_type'] = user_type
        return redirect(url_for('home'))
    else:
        flash('Invalid credentials. Please try again or sign up.', 'error')
        return redirect(url_for('login_page'))
    
@app.route('/adminlogin')
def adminlogin():   
    return render_template('adminlogin.html')

@app.route('/adminlogin1', methods=['POST'])
def adminlogin1():
    username = request.form['username']
    password = request.form['password']
      # Assuming admin login is for Faculty only

    select_query = "SELECT * FROM user WHERE username = %s AND password = %s"
    cursor.execute(select_query, (username, password))
    user = cursor.fetchone()

    if user:
        session['username'] = username
        
        return redirect(url_for('admin'))
    else:
        flash('Invalid admin credentials. Please try again.', 'error')
        return redirect(url_for('adminlogin'))

@app.route('/signup_submit', methods=['POST'])
def signup_submit():
    error = None
    success = None
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']

    if not re.search('[a-zA-Z]', username):
        error = 'Username must contain at least one alphabetic letter'
        return render_template('signup.html', error=error, username=username, user_type=user_type)

    if len(password) < 6:
        error = 'Password must be at least 6 characters long'
        return render_template('signup.html', error=error, username=username, user_type=user_type)

    select_query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(select_query, (username,))
    if cursor.fetchone():
        error = 'This username is already taken'
        return render_template('signup.html', error=error, username=username, user_type=user_type)

    insert_query = "INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (username, password, user_type))
    db.commit()
    success = 'Account created successfully! Please log in.'
    return render_template('login.html', success=success)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))

@app.route('/submitpublication')
@login_required
def submitpublication():
    return render_template('submit.html', user_type=session.get('user_type'))

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        data = (
            request.form['faculty_name'],
            request.form['department'],
            request.form['title'],
            request.form['pub_type'],
            request.form['publisher'],
            request.form['publisher_email'],
            request.form['publication_year'],
            request.form['doi_or_link']
        )
        cursor.execute("""
            INSERT INTO publications 
            (faculty_name, department, title, pub_type, publisher, publisher_email, publication_year, doi_or_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        db.commit()
        flash('Publication submitted successfully!', 'success')
        return redirect(url_for('view_publications'))
    return render_template('submit.html', user_type=session.get('user_type'))

@app.route('/view_publications')
@login_required
def view_publications():
    cursor.execute("SELECT * FROM publications")
    records = cursor.fetchall()
    return render_template('view.html', records=records, user_type=session.get('user_type'))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %b %Y, %I:%M %p'):
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return value.strftime(format)

@app.route('/admin')
@login_required
def admin():
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    cursor.execute("SELECT * FROM publications")
    records = cursor.fetchall()
    return render_template('admin.html', records=records, user_type=session.get('user_type'))

@app.route('/send_remark', methods=['POST'])
@login_required
def send_remark():
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    sender_gmail = request.form['sender_gmail']
    publisher_email = request.form['publisher_email']
    remark = request.form['remark']
    title = request.form['title']

    msg = Message(
        subject=f"Remark on Publication: {title}",
        sender=app.config['MAIL_USERNAME'],
        recipients=[publisher_email]
    )
    msg.body = f"From: {sender_gmail}\n\nHere is a remark regarding the publication titled '{title}':\n\n{remark}\n\nRegards,\n{sender_gmail}"

    try:
        mail.send(msg)
        flash('Remark sent successfully!', 'success')
        return redirect(url_for('admin'))
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/edit/<int:pub_id>', methods=['GET'])
@login_required
def edit_publication(pub_id):
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    cursor.execute("SELECT * FROM publications WHERE pub_id = %s", (pub_id,))
    record = cursor.fetchone()
    return render_template('edit_publication.html', record=record, user_type=session.get('user_type'))

@app.route('/update/<int:pub_id>', methods=['POST'])
@login_required
def update_publication(pub_id):
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    faculty = request.form['faculty']
    department = request.form['department']
    title = request.form['title']
    type_ = request.form['type']
    publisher = request.form['publisher']
    publisher_email = request.form['publisher_email']
    year = request.form['year']
    link = request.form['link']
    
    cursor.execute("""
        UPDATE publications 
        SET faculty_name=%s, department=%s, title=%s, pub_type=%s, publisher=%s, publisher_email=%s, publication_year=%s, doi_or_link=%s 
        WHERE pub_id=%s
    """, (faculty, department, title, type_, publisher, publisher_email, year, link, pub_id))
    db.commit()
    flash('Publication updated successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete/<int:pub_id>', methods=['POST'])
@login_required
def delete_publication(pub_id):
    if session.get('user_type') != 'Faculty':
        flash('Access denied. Faculty only.', 'error')
        return redirect(url_for('home'))
    cursor.execute("DELETE FROM publications WHERE pub_id = %s", (pub_id,))
    db.commit()
    flash('Publication deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/view')
@login_required
def view():
    return redirect(url_for('view_publications'))

if __name__ == '__main__':
    app.run(debug=True)