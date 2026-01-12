"""
Simple Flask Application for Library Management System
This is a simplified version that works with our SQLite database
"""

import sqlite3
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'library-management-secret-key'

# Database configuration
DATABASE = os.path.join(os.path.dirname(__file__), 'library.db')

_schema_checked = False


def ensure_schema(conn):
    global _schema_checked
    if _schema_checked:
        return

    # Check books table
    columns = [row['name'] for row in conn.execute('PRAGMA table_info(books)').fetchall()]
    if not columns:
        return
    if 'price' not in columns:
        conn.execute('ALTER TABLE books ADD COLUMN price REAL DEFAULT 0.0')
        conn.commit()

    # Check users table
    user_columns = [row['name'] for row in conn.execute('PRAGMA table_info(users)').fetchall()]
    if 'student_id' not in user_columns:
        conn.execute('ALTER TABLE users ADD COLUMN student_id VARCHAR(20)')
        conn.commit()

    _schema_checked = True

def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        ensure_schema(db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_required(f):
    """Login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Admin required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - Admin only"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Only allow admin users to login
            if user['user_type'] != 'admin':
                flash('Only administrators can access this system', 'danger')
                return render_template('login.html')
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['user_type'] = user['user_type']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - Student Management Overview"""
    db = get_db()
    
    # Get statistics
    total_books = db.execute('SELECT COUNT(*) as count FROM books WHERE is_active = 1').fetchone()['count']
    total_users = db.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1').fetchone()['count']
    issued_books = db.execute('SELECT COUNT(*) as count FROM transactions WHERE status = "issued"').fetchone()['count']
    overdue_books = db.execute('SELECT COUNT(*) as count FROM transactions WHERE status = "issued" AND due_date < ?', (datetime.now(),)).fetchone()['count']
    
    # Get students currently borrowing books (who are taking books home)
    students_with_books = db.execute('''
        SELECT DISTINCT u.id, u.full_name, u.username, u.email, u.phone,
               COUNT(t.id) as active_books_count
        FROM users u
        JOIN transactions t ON u.id = t.user_id
        WHERE t.status = 'issued' AND u.is_active = 1
        GROUP BY u.id, u.full_name, u.username, u.email, u.phone
        ORDER BY u.full_name
    ''').fetchall()
    
    # Recent transactions with full details
    recent_transactions = db.execute('''
        SELECT t.*, u.full_name, u.username, u.email, u.phone, b.title, b.author, b.isbn
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        ORDER BY t.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Get unpaid fines
    unpaid_fines = db.execute('''
        SELECT f.*, u.full_name, u.username, b.title
        FROM fines f
        JOIN transactions t ON f.transaction_id = t.id
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        WHERE f.status = 'unpaid'
        ORDER BY f.created_at DESC
    ''').fetchall()
    
    # Low stock books
    low_stock_books = db.execute('''
        SELECT * FROM books 
        WHERE is_active = 1 AND available_copies <= 1
        LIMIT 5
    ''').fetchall()
    
    return render_template('dashboard.html',
                         total_books=total_books,
                         total_users=total_users,
                         issued_books=issued_books,
                         overdue_books=overdue_books,
                         students_with_books=students_with_books,
                         recent_transactions=recent_transactions,
                         unpaid_fines=unpaid_fines,
                         low_stock_books=low_stock_books)

@app.route('/books')
@login_required
def books():
    """Books list"""
    db = get_db()
    search = request.args.get('search', '')
    
    query = 'SELECT * FROM books WHERE is_active = 1'
    params = []
    
    if search:
        query += ' AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)'
        params = [f'%{search}%', f'%{search}%', f'%{search}%']
    
    query += ' ORDER BY title'
    
    books = db.execute(query, params).fetchall()
    return render_template('books/list_simple.html', books=books, search=search)

@app.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    """Add book"""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        publisher = request.form.get('publisher', '')
        publication_year = request.form.get('publication_year', '')
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        total_copies = request.form.get('total_copies', 1, type=int)
        price = request.form.get('price', 0, type=float)
        location = request.form.get('location', '')
        
        db = get_db()
        
        # Check if ISBN exists
        existing = db.execute('SELECT id FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if existing:
            flash('A book with this ISBN already exists', 'danger')
            return render_template('books/add_simple.html')
        
        # Insert book
        db.execute('''
            INSERT INTO books (title, author, isbn, publisher, publication_year, category, description, total_copies, available_copies, location, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, author, isbn, publisher, publication_year, category, description, total_copies, total_copies, location, price))
        db.commit()
        
        flash(f'Book "{title}" added successfully', 'success')
        return redirect(url_for('books'))
    
    return render_template('books/add_simple.html')

@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    """Edit book"""
    db = get_db()
    
    # Get book
    book = db.execute('SELECT * FROM books WHERE id = ? AND is_active = 1', (book_id,)).fetchone()
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('books'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher', '')
        publication_year = request.form.get('publication_year', '')
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        total_copies = request.form.get('total_copies', type=int)
        price = request.form.get('price', 0, type=float)
        location = request.form.get('location', '')
        
        # Validation
        if not title or not author or not isbn:
            flash('Title, Author, and ISBN are required', 'danger')
            return render_template('books/edit.html', book=book)
        
        # Check if ISBN already exists (excluding current book)
        existing_book = db.execute('SELECT id FROM books WHERE isbn = ? AND id != ?', (isbn, book_id)).fetchone()
        if existing_book:
            flash('A book with this ISBN already exists', 'danger')
            return render_template('books/edit.html', book=book)
        
        # Update book
        old_total = book['total_copies']
        db.execute(''' 
            UPDATE books SET title = ?, author = ?, isbn = ?, publisher = ?, 
               publication_year = ?, category = ?, description = ?, 
               total_copies = ?, location = ?, price = ?
            WHERE id = ?
        ''', (title, author, isbn, publisher, publication_year, category, description, total_copies, location, price, book_id))
        
        # Update available copies if total changed
        if total_copies > old_total:
            db.execute('UPDATE books SET available_copies = available_copies + ? WHERE id = ?', 
                      (total_copies - old_total, book_id))
        elif total_copies < old_total:
            # Don't let available copies exceed total
            issued_copies = old_total - book['available_copies']
            db.execute('UPDATE books SET available_copies = MAX(0, ?) WHERE id = ?', 
                      (total_copies - issued_copies, book_id))
        
        db.commit()
        
        flash(f'Book "{title}" updated successfully', 'success')
        return redirect(url_for('books'))
    
    return render_template('books/edit.html', book=book)

@app.route('/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    """Delete book"""
    db = get_db()
    
    # Get book
    book = db.execute('SELECT * FROM books WHERE id = ? AND is_active = 1', (book_id,)).fetchone()
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('books'))
    
    # Check if book has any active transactions
    active_transactions = db.execute('''
        SELECT COUNT(*) as count FROM transactions 
        WHERE book_id = ? AND status = 'issued'
    ''', (book_id,)).fetchone()['count']
    
    if active_transactions > 0:
        flash('Cannot delete book with active transactions', 'danger')
        return redirect(url_for('books'))
    
    # Soft delete (mark as inactive)
    db.execute('UPDATE books SET is_active = 0 WHERE id = ?', (book_id,))
    db.commit()
    
    flash(f'Book "{book["title"]}" deleted successfully', 'success')
    return redirect(url_for('books'))

@app.route('/transactions')
@login_required
def transactions():
    """Transactions list"""
    db = get_db()
    
    query = '''
        SELECT t.*, u.full_name, b.title 
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        ORDER BY t.created_at DESC
    '''
    
    transactions = db.execute(query).fetchall()
    
    return render_template('transactions/list_simple.html', transactions=transactions)

@app.route('/transactions/issue', methods=['GET', 'POST'])
@admin_required
def issue_book():
    """Issue book"""
    db = get_db()
    
    if request.method == 'POST':
        book_id = request.form['book_id']
        user_id = request.form['user_id']
        due_days = request.form.get('due_days', 14, type=int)
        notes = request.form.get('notes', '')
        
        # Check book availability
        book = db.execute('SELECT * FROM books WHERE id = ? AND available_copies > 0', (book_id,)).fetchone()
        if not book:
            flash('Book is not available', 'danger')
            return render_template('transactions/issue_simple.html')
        
        # Check if user already has this book
        existing = db.execute('''
            SELECT id FROM transactions 
            WHERE user_id = ? AND book_id = ? AND status = 'issued'
        ''', (user_id, book_id)).fetchone()
        
        if existing:
            flash('User already has this book issued', 'danger')
            return render_template('transactions/issue_simple.html')
        
        # Create transaction
        due_date = datetime.now() + timedelta(days=due_days)
        db.execute('''
            INSERT INTO transactions (user_id, book_id, due_date, notes, status)
            VALUES (?, ?, ?, ?, 'issued')
        ''', (user_id, book_id, due_date, notes))
        
        # Update book availability
        db.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id = ?', (book_id,))
        db.commit()
        
        flash(f'Book "{book["title"]}" issued successfully', 'success')
        return redirect(url_for('transactions'))
    
    # Get available books and users
    books = db.execute('SELECT * FROM books WHERE is_active = 1 AND available_copies > 0 ORDER BY title').fetchall()
    users = db.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY full_name').fetchall()
    
    return render_template('transactions/issue_simple.html', books=books, users=users)

@app.route('/transactions/return/<int:transaction_id>', methods=['POST'])
@login_required
def return_book(transaction_id):
    """Return book"""
    db = get_db()
    
    # Get transaction
    transaction = db.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    if not transaction or transaction['status'] == 'returned':
        flash('Invalid transaction', 'danger')
        return redirect(url_for('transactions'))
    
    # Check permissions (admin can return any book, users can only return their own)
    if session['user_type'] != 'admin' and transaction['user_id'] != session['user_id']:
        flash('Unauthorized', 'danger')
        return redirect(url_for('transactions'))
    
    # Update transaction
    return_date = datetime.now()
    status = 'returned'
    fine_amount = 0
    
    # Check if overdue
    try:
        due_date = datetime.strptime(transaction['due_date'], '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        due_date = datetime.strptime(transaction['due_date'], '%Y-%m-%d %H:%M:%S')
    
    if return_date > due_date:
        days_late = (return_date - due_date).days
        fine_amount = days_late * 1.0  # $1 per day
        
        # Create fine record
        db.execute('''
            INSERT INTO fines (transaction_id, amount, per_day_rate, days_late, total_amount, status)
            VALUES (?, ?, ?, ?, ?, 'unpaid')
        ''', (transaction_id, 1.0, 1.0, days_late, fine_amount))
        
        flash(f'Book returned with fine of ₹{fine_amount:.2f} for {days_late} days late', 'warning')
    else:
        flash('Book returned successfully', 'success')
    
    db.execute('UPDATE transactions SET return_date = ?, status = ? WHERE id = ?', (return_date, status, transaction_id))
    
    # Update book availability
    db.execute('UPDATE books SET available_copies = available_copies + 1 WHERE id = ?', (transaction['book_id'],))
    db.commit()
    
    return redirect(url_for('transactions'))

@app.route('/students')
@admin_required
def students():
    """Students list"""
    db = get_db()
    search = request.args.get('search', '')
    
    query = '''
        SELECT u.*, 
               COUNT(CASE WHEN t.status = 'issued' THEN 1 END) as active_books_count,
               COALESCE(SUM(CASE WHEN f.status = 'unpaid' THEN f.total_amount ELSE 0 END), 0) as total_fines
        FROM users u
        LEFT JOIN transactions t ON u.id = t.user_id
        LEFT JOIN fines f ON t.id = f.transaction_id
        WHERE u.is_active = 1 AND u.user_type = 'student'
    '''
    params = []
    
    if search:
        query += ' AND (u.full_name LIKE ? OR u.username LIKE ? OR u.email LIKE ?)'
        params = [f'%{search}%', f'%{search}%', f'%{search}%']
    
    query += ' GROUP BY u.id, u.student_id, u.full_name, u.username, u.email, u.phone, u.address, u.password_hash, u.user_type, u.is_active'
    query += ' ORDER BY u.full_name'
    
    students = db.execute(query, params).fetchall()
    return render_template('students/list.html', students=students, search=search)

@app.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add student"""
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        student_id = request.form.get('student_id', '').strip()
        
        # Get book details
        book_title = request.form.get('book_title', '')
        book_author = request.form.get('book_author', '')
        book_isbn = request.form.get('book_isbn', '')
        book_category = request.form.get('book_category', '')
        book_description = request.form.get('book_description', '')
        book_price = request.form.get('book_price', default=None, type=float)
        
        # Validation
        if not full_name or not email:
            flash('Full Name and Email are required', 'danger')
            return render_template('students/add.html')
        
        db = get_db()
        
        # Check if student ID already exists (if provided)
        if student_id and db.execute('SELECT id FROM users WHERE student_id = ?', (student_id,)).fetchone():
            flash('Student ID already exists', 'danger')
            return render_template('students/add.html')
        
        # Generate username from full name
        base_username = full_name.lower().replace(' ', '.').replace('-', '.')
        username = base_username
        counter = 1
        
        # Ensure username is unique
        while db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Check if email already exists
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            flash('Email already exists', 'danger')
            return render_template('students/add.html')
        
        # Generate random password
        import random
        import string
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Create new student
        from werkzeug.security import generate_password_hash
        db.execute('''
            INSERT INTO users (student_id, username, email, password_hash, full_name, phone, address, user_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'student')
        ''', (student_id if student_id else None, username, email, generate_password_hash(password), full_name, phone, address))
        db.commit()
        
        # Get the student database ID
        student_db_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # If book details are provided, add the book
        if book_title and book_author:
            # Check if book already exists
            existing_book = db.execute(
                'SELECT id FROM books WHERE title = ? AND author = ?',
                (book_title, book_author),
            ).fetchone()

            if existing_book:
                book_id = existing_book['id']
                if book_price is not None:
                    db.execute('UPDATE books SET price = ? WHERE id = ?', (book_price, book_id))
                    db.commit()
            else:
                # Add the book
                db.execute('''
                    INSERT INTO books (title, author, isbn, category, description, total_copies, available_copies, price)
                    VALUES (?, ?, ?, ?, ?, 1, 1, ?)
                ''', (book_title, book_author, book_isbn, book_category, book_description, book_price if book_price is not None else 0))
                db.commit()

                # Get the book ID
                book_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            # Issue the book to the student
            due_date = datetime.now() + timedelta(days=14)

            db.execute('''
                INSERT INTO transactions (user_id, book_id, due_date, status)
                VALUES (?, ?, ?, 'issued')
            ''', (student_db_id, book_id, due_date))

            # Update book availability
            db.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id = ?', (book_id,))
            db.commit()
        
        flash(f'Student "{full_name}" added successfully! Username: {username}, Password: {password}', 'success')
        return redirect(url_for('students'))
    
    return render_template('students/add.html')

@app.route('/students/<int:student_id>')
@admin_required
def view_student(student_id):
    """View student details"""
    db = get_db()
    student = db.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (student_id,)).fetchone()
    
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('students'))
    
    # Get transaction history for this student
    transactions = db.execute('''
        SELECT t.*, b.title, b.author,
               f.total_amount as fine_amount, f.status as fine_status
        FROM transactions t
        JOIN books b ON t.book_id = b.id
        LEFT JOIN fines f ON t.id = f.transaction_id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        LIMIT 10
    ''', (student_id,)).fetchall()
    
    # Get student's total fines
    total_fines = db.execute('''
        SELECT COALESCE(SUM(total_amount), 0) as total
        FROM fines f
        JOIN transactions t ON f.transaction_id = t.id
        WHERE t.user_id = ? AND f.status = 'unpaid'
    ''', (student_id,)).fetchone()['total']
    
    # Calculate statistics
    total_transactions = len(transactions)
    active_transactions = len([t for t in transactions if t['status'] == 'issued'])
    
    # Convert student to dict to add total_fines
    student_dict = dict(student)
    student_dict['total_fines'] = total_fines
    
    return render_template('students/view.html', 
                         student=student_dict, 
                         transactions=transactions,
                         total_transactions=total_transactions,
                         active_transactions=active_transactions)

@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student"""
    db = get_db()
    
    # Get student
    student = db.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (student_id,)).fetchone()
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('students'))
    
    # Prevent editing admin users
    if student['user_type'] == 'admin':
        flash('Cannot edit administrator users', 'danger')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        user_type = request.form.get('user_type', 'student')
        student_id_field = request.form.get('student_id', '').strip()
        
        # Validation
        if not email or not full_name:
            flash('Email and Full Name are required', 'danger')
            return render_template('students/edit.html', student=student)
        
        # Check if email already exists (excluding current student)
        existing_student = db.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, student_id)).fetchone()
        if existing_student:
            flash('Email already exists', 'danger')
            return render_template('students/edit.html', student=student)
        
        # Check if student ID already exists (if provided and different from current)
        if student_id_field:
            current_student_id = student['student_id']
            if student_id_field != current_student_id:
                existing_id = db.execute('SELECT id FROM users WHERE student_id = ? AND id != ?', (student_id_field, student_id)).fetchone()
                if existing_id:
                    flash('Student ID already exists', 'danger')
                    return render_template('students/edit.html', student=student)
        
        # Update student
        db.execute('''
            UPDATE users SET email = ?, full_name = ?, phone = ?, address = ?, user_type = ?, student_id = ?
            WHERE id = ?
        ''', (email, full_name, phone, address, user_type, student_id_field if student_id_field else None, student_id))
        db.commit()
        
        flash(f'Student "{full_name}" updated successfully', 'success')
        return redirect(url_for('students'))
    
    return render_template('students/edit.html', student=student)

@app.route('/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete student"""
    db = get_db()
    
    # Get student
    student = db.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (student_id,)).fetchone()
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('students'))
    
    # Prevent deleting admin users
    if student['user_type'] == 'admin':
        flash('Cannot delete administrator users', 'danger')
        return redirect(url_for('students'))
    
    # Prevent deleting self
    if student['id'] == session['user_id']:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('students'))
    
    # Check if student has any active transactions
    active_transactions = db.execute('''
        SELECT COUNT(*) as count FROM transactions 
        WHERE user_id = ? AND status = 'issued'
    ''', (student_id,)).fetchone()['count']
    
    if active_transactions > 0:
        flash('Cannot delete student with active transactions', 'danger')
        return redirect(url_for('students'))
    
    # Soft delete (mark as inactive)
    db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (student_id,))
    db.commit()
    
    flash(f'Student "{student["full_name"]}" deleted successfully', 'success')
    return redirect(url_for('students'))

@app.route('/reports')
@login_required
def reports():
    """Reports dashboard"""
    return render_template('reports/dashboard_simple.html')

@app.route('/fines')
@login_required
def fines():
    """Fines management"""
    db = get_db()
    
    # Get all fines with details
    fines = db.execute('''
        SELECT f.*, u.full_name, u.username, u.email, u.phone,
               b.title, b.author, b.isbn,
               t.created_at as issue_date, t.due_date, t.return_date
        FROM fines f
        JOIN transactions t ON f.transaction_id = t.id
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        ORDER BY f.created_at DESC
    ''').fetchall()
    
    return render_template('fines/list.html', fines=fines)

@app.route('/fines/pay/<int:fine_id>', methods=['POST'])
@login_required
def pay_fine(fine_id):
    """Pay fine"""
    db = get_db()
    
    # Get fine
    fine = db.execute('''
        SELECT f.*, u.full_name, b.title
        FROM fines f
        JOIN transactions t ON f.transaction_id = t.id
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        WHERE f.id = ?
    ''', (fine_id,)).fetchone()
    
    if not fine:
        flash('Fine not found', 'danger')
        return redirect(url_for('fines'))
    
    if fine['status'] == 'paid':
        flash('Fine already paid', 'info')
        return redirect(url_for('fines'))
    
    # Mark fine as paid
    db.execute('UPDATE fines SET status = "paid", paid_date = ? WHERE id = ?', 
              (datetime.now(), fine_id))
    db.commit()
    
    flash(f'Fine of ₹{fine["total_amount"]:.2f} paid successfully for {fine["full_name"]}', 'success')
    return redirect(url_for('fines'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
