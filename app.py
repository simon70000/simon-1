from flask import Flask, render_template
import sqlite3
from flask import g, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super secret key'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def user_login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('user_login'))
        return view(**kwargs)
    return wrapped_view

def admin_login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for('admin_login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        admin = db.execute(
            'SELECT * FROM admins WHERE username = ?', (username,)
        ).fetchone()

        if admin is None:
            error = 'Incorrect username.'
        elif not check_password_hash(admin['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['admin_id'] = admin['id']
            return redirect(url_for('admin_dashboard'))

        flash(error)

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    db = get_db()
    requests = db.execute(
        'SELECT id, event_title, department, student_id, status FROM event_requests'
    ).fetchall()
    events = db.execute(
        'SELECT id, title, description, registration_deadline FROM events'
    ).fetchall()
    return render_template('admin_dashboard.html', requests=requests, events=events)

@app.route('/admin/update_request_status/<int:id>/<status>')
@admin_login_required
def update_request_status(id, status):
    db = get_db()
    db.execute(
        'UPDATE event_requests SET status = ? WHERE id = ?',
        (status, id)
    )
    db.commit()
    flash('Event request status updated.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_event/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_event(id):
    db = get_db()
    event = db.execute('SELECT * FROM events WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        registration_deadline = request.form['registration_deadline']

        db.execute(
            'UPDATE events SET title = ?, description = ?, registration_deadline = ? WHERE id = ?',
            (title, description, registration_deadline, id)
        )
        db.commit()
        flash('Event updated successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_event.html', event=event)

@app.route('/admin/delete_event/<int:id>')
@admin_login_required
def delete_event(id):
    db = get_db()
    db.execute('DELETE FROM events WHERE id = ?', (id,))
    db.commit()
    flash('Event deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_event', methods=['POST'])
@admin_login_required
def add_event():
    title = request.form['title']
    description = request.form['description']
    registration_deadline = request.form['registration_deadline']

    db = get_db()
    db.execute(
        'INSERT INTO events (title, description, registration_deadline) VALUES (?, ?, ?)',
        (title, description, registration_deadline)
    )
    db.commit()
    flash('Event added successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE student_id = ?', (student_id,)
        ).fetchone()

        if user is None:
            error = 'Incorrect student ID.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('user_dashboard'))

        flash(error)

    return render_template('user_login.html')

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

    if admin_id is None:
        g.admin = None
    else:
        g.admin = get_db().execute(
            'SELECT * FROM admins WHERE id = ?', (admin_id,)
        ).fetchone()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@user_login_required
def user_dashboard():
    db = get_db()
    events = db.execute(
        'SELECT title, description, registration_deadline FROM events'
    ).fetchall()
    return render_template('user_dashboard.html', events=events)

@app.route('/user/submit_request', methods=['POST'])
@user_login_required
def submit_request():
    event_title = request.form['event_title']
    department = request.form['department']
    student_id = request.form['student_id']
    event_description = request.form['event_description']
    rehearsal_date = request.form['rehearsal_date']
    participants_names = request.form['participants_names']
    practice_timing = request.form['practice_timing']

    db = get_db()
    db.execute(
        'INSERT INTO event_requests (event_title, department, student_id, event_description, rehearsal_date, participants_names, practice_timing) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (event_title, department, student_id, event_description, rehearsal_date, participants_names, practice_timing)
    )
    db.commit()
    flash('Event request submitted successfully!')
    return redirect(url_for('user_dashboard'))

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        db = get_db()
        error = None

        if not student_id:
            error = 'Student ID is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (student_id, password) VALUES (?, ?)",
                    (student_id, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {student_id} is already registered."
            else:
                flash("Registration successful!")
                return redirect(url_for("user_login"))

        flash(error)

    return render_template('user_register.html')

if __name__ == '__main__':
    app.run(debug=True)
