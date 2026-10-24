# import os
# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from flask_mysqldb import MySQL
# from werkzeug.security import generate_password_hash, check_password_hash
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# app.secret_key = os.getenv('SECRET_KEY')

# # Database Config (Uses Environment Variables)
# app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
# app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
# app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
# app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'event_management')

# mysql = MySQL(app)

# @app.route('/')
# def index():
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM events")
#     events = cur.fetchall()
#     cur.close()
#     return render_template('index.html', events=events)

# # (Add login, register, book_event, admin routes here)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)

import os
from functools import wraps
from datetime import datetime

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-fallback-key-change-me')

# ---------- DATABASE CONFIG ----------
app.config['MYSQL_HOST']     = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']     = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']       = os.getenv('MYSQL_DB', 'event_management')

mysql = MySQL(app)


# ============================================================
# DECORATORS (Role-Based Access Control)
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# PUBLIC ROUTES
# ============================================================
@app.route('/')
def index():
    search   = request.args.get('q', '').strip()
    category = request.args.get('category', type=int)

    cur = mysql.connection.cursor()
    sql = """
        SELECT e.id, e.title, e.description, e.event_date, e.event_time,
               e.venue, e.capacity, c.name AS category_name,
               (SELECT COUNT(*) FROM bookings b
                WHERE b.event_id = e.id AND b.status = 'confirmed') AS booked
        FROM events e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (e.title LIKE %s OR e.venue LIKE %s OR e.description LIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    if category:
        sql += " AND e.category_id = %s"
        params.append(category)
    sql += " ORDER BY e.event_date ASC"

    cur.execute(sql, params)
    events = cur.fetchall()

    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()

    return render_template('index.html',
                           events=events,
                           categories=categories,
                           current_search=search,
                           current_category=category)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.id, e.title, e.description, e.event_date, e.event_time,
               e.venue, e.capacity, c.name,
               (SELECT COUNT(*) FROM bookings b
                WHERE b.event_id = e.id AND b.status = 'confirmed') AS booked
        FROM events e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.id = %s
    """, (event_id,))
    event = cur.fetchone()

    if not event:
        cur.close()
        flash('Event not found.', 'danger')
        return redirect(url_for('index'))

    already_booked = False
    if 'user_id' in session:
        cur.execute("""SELECT id, status FROM bookings
                       WHERE user_id=%s AND event_id=%s""",
                    (session['user_id'], event_id))
        row = cur.fetchone()
        if row and row[1] == 'confirmed':
            already_booked = True

    cur.close()
    return render_template('event_detail.html',
                           event=event,
                           already_booked=already_booked)


# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        confirm  = request.form['confirm']

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash('Email already registered.', 'danger')
                cur.close()
                return redirect(url_for('register'))

            hashed = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s,%s,%s,'user')",
                (name, email, hashed)
            )
            mysql.connection.commit()
            cur.close()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, password_hash, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session['user_id']   = user[0]
            session['user_name'] = user[1]
            session['role']      = user[3]
            flash(f'Welcome back, {user[1]}!', 'success')
            return redirect(url_for('admin_dashboard' if user[3] == 'admin' else 'index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ============================================================
# USER BOOKINGS
# ============================================================
@app.route('/book/<int:event_id>', methods=['POST'])
@login_required
def book_event(event_id):
    cur = mysql.connection.cursor()

    # Check event exists + capacity
    cur.execute("""SELECT e.capacity,
                   (SELECT COUNT(*) FROM bookings b
                    WHERE b.event_id=e.id AND b.status='confirmed')
                   FROM events e WHERE e.id=%s""", (event_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        flash('Event not found.', 'danger')
        return redirect(url_for('index'))

    capacity, booked = row
    if booked >= capacity:
        cur.close()
        flash('Sorry — this event is fully booked.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))

    # Check duplicate
    cur.execute("SELECT id, status FROM bookings WHERE user_id=%s AND event_id=%s",
                (session['user_id'], event_id))
    existing = cur.fetchone()

    if existing:
        if existing[1] == 'confirmed':
            cur.close()
            flash('You already booked this event.', 'warning')
            return redirect(url_for('event_detail', event_id=event_id))
        else:
            # Re-activate cancelled booking
            cur.execute("UPDATE bookings SET status='confirmed', booking_date=NOW() WHERE id=%s",
                        (existing[0],))
    else:
        cur.execute("INSERT INTO bookings (user_id, event_id, status) VALUES (%s,%s,'confirmed')",
                    (session['user_id'], event_id))

    mysql.connection.commit()
    cur.close()
    flash('🎉 Booking confirmed!', 'success')
    return redirect(url_for('my_bookings'))


@app.route('/my-bookings')
@login_required
def my_bookings():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.id, e.title, e.event_date, e.event_time, e.venue,
               b.status, b.booking_date, e.id
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """, (session['user_id'],))
    bookings = cur.fetchall()
    cur.close()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s AND user_id=%s",
                (booking_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Booking cancelled.', 'info')
    return redirect(url_for('my_bookings'))


# ============================================================
# ADMIN ROUTES
# ============================================================
@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.id, e.title, e.event_date, e.venue, e.capacity,
               c.name,
               (SELECT COUNT(*) FROM bookings b
                WHERE b.event_id=e.id AND b.status='confirmed')
        FROM events e
        LEFT JOIN categories c ON e.category_id=c.id
        ORDER BY e.event_date DESC
    """)
    events = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM events");     total_events     = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users");      total_users      = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bookings");   total_bookings   = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM categories"); total_categories = cur.fetchone()[0]
    cur.close()

    return render_template('admin_dashboard.html',
                           events=events,
                           total_events=total_events,
                           total_users=total_users,
                           total_bookings=total_bookings,
                           total_categories=total_categories)


@app.route('/admin/event/new', methods=['GET', 'POST'])
@admin_required
def add_event():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()

    if request.method == 'POST':
        title       = request.form['title'].strip()
        description = request.form['description'].strip()
        date        = request.form['event_date']
        time        = request.form['event_time']
        venue       = request.form['venue'].strip()
        category_id = request.form.get('category_id') or None
        capacity    = request.form['capacity']

        if not all([title, date, time, venue, capacity]):
            flash('Please fill all required fields.', 'danger')
        else:
            cur.execute("""
                INSERT INTO events
                (title, description, event_date, event_time, venue, category_id, capacity)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (title, description, date, time, venue, category_id, capacity))
            mysql.connection.commit()
            cur.close()
            flash('✅ Event added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    cur.close()
    return render_template('admin_event_form.html',
                           categories=categories,
                           event=None,
                           action='Add')


@app.route('/admin/event/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        title       = request.form['title'].strip()
        description = request.form['description'].strip()
        date        = request.form['event_date']
        time        = request.form['event_time']
        venue       = request.form['venue'].strip()
        category_id = request.form.get('category_id') or None
        capacity    = request.form['capacity']

        cur.execute("""
            UPDATE events SET title=%s, description=%s, event_date=%s,
                   event_time=%s, venue=%s, category_id=%s, capacity=%s
            WHERE id=%s
        """, (title, description, date, time, venue, category_id, capacity, event_id))
        mysql.connection.commit()
        cur.close()
        flash('✅ Event updated.', 'success')
        return redirect(url_for('admin_dashboard'))

    cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cur.fetchone()

    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()

    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_event_form.html',
                           categories=categories,
                           event=event,
                           action='Edit')


@app.route('/admin/event/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM events WHERE id=%s", (event_id,))
    mysql.connection.commit()
    cur.close()
    flash('Event deleted.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name'].strip()
        if name:
            try:
                cur.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
                mysql.connection.commit()
                flash(f'Category "{name}" added.', 'success')
            except Exception:
                flash('Category already exists.', 'warning')
        return redirect(url_for('admin_categories'))

    cur.execute("""
        SELECT c.id, c.name,
               (SELECT COUNT(*) FROM events e WHERE e.category_id=c.id)
        FROM categories c ORDER BY c.name
    """)
    cats = cur.fetchall()
    cur.close()
    return render_template('admin_categories.html', categories=cats)


@app.route('/admin/category/<int:cat_id>/delete', methods=['POST'])
@admin_required
def delete_category(cat_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categories WHERE id=%s", (cat_id,))
    mysql.connection.commit()
    cur.close()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin_categories'))


@app.route('/admin/event/<int:event_id>/participants')
@admin_required
def event_participants(event_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT title FROM events WHERE id=%s", (event_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        flash('Event not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    event_title = row[0]

    cur.execute("""
        SELECT u.name, u.email, b.booking_date, b.status
        FROM bookings b JOIN users u ON b.user_id=u.id
        WHERE b.event_id=%s ORDER BY b.booking_date DESC
    """, (event_id,))
    participants = cur.fetchall()
    cur.close()
    return render_template('event_participants.html',
                           participants=participants,
                           event_title=event_title)


# ============================================================
# SECURE ONE-TIME ADMIN CREATION
# ============================================================
@app.route('/setup-admin')
def setup_admin():
    email    = 'admin@eventhub.com'
    password = 'Admin@12345'
    name     = 'Admin'

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close()
        return "⚠️ Admin already exists. Log in at /login"

    hashed = generate_password_hash(password)
    cur.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s,%s,%s,'admin')",
        (name, email, hashed)
    )
    mysql.connection.commit()
    cur.close()
    return f"✅ Admin created: {email} / {password}<br>DELETE this route now!"


# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)