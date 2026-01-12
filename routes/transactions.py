"""
Transaction Management Routes
Handles book issue, return, and transaction management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.models import db, Book, Transaction, Fine, User

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
@login_required
def list_transactions():
    """Display list of all transactions"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    user_id = request.args.get('user_id', '')
    
    # Build query
    query = Transaction.query
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    # Filter by user (admin only)
    if current_user.user_type == 'admin' and user_id:
        query = query.filter_by(user_id=user_id)
    elif current_user.user_type != 'admin':
        # Students can only see their own transactions
        query = query.filter_by(user_id=current_user.id)
    
    # Pagination
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get users for filter dropdown (admin only)
    users = []
    if current_user.user_type == 'admin':
        users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    
    return render_template('transactions/list.html', 
                         transactions=transactions, 
                         status=status,
                         user_id=user_id,
                         users=users)

@transactions_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_book():
    """Issue a book to a user"""
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        user_id = request.form.get('user_id')
        due_days = request.form.get('due_days', type=int)
        notes = request.form.get('notes')
        
        # Validation
        if not book_id or not user_id:
            flash('Book and User are required', 'danger')
            return render_template('transactions/issue.html')
        
        # Get book and user
        book = Book.query.get_or_404(book_id)
        user = User.query.get_or_404(user_id)
        
        # Check if book is available
        if not book.is_available():
            flash('Book is not available for issue', 'danger')
            return render_template('transactions/issue.html')
        
        # Check if user already has this book issued
        existing_transaction = Transaction.query.filter_by(
            user_id=user_id, 
            book_id=book_id, 
            status='issued'
        ).first()
        
        if existing_transaction:
            flash('User already has this book issued', 'danger')
            return render_template('transactions/issue.html')
        
        # Set default due days
        if not due_days or due_days <= 0:
            due_days = 14  # Default 2 weeks
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            book_id=book_id,
            due_date=datetime.utcnow() + timedelta(days=due_days),
            notes=notes,
            status='issued'
        )
        
        # Update book availability
        book.available_copies -= 1
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Book "{book.title}" issued to {user.full_name} successfully', 'success')
        return redirect(url_for('transactions.view_transaction', transaction_id=transaction.id))
    
    # Get available books and active users
    books = Book.query.filter_by(is_active=True).filter(Book.available_copies > 0).order_by(Book.title).all()
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    
    return render_template('transactions/issue.html', books=books, users=users)

@transactions_bp.route('/<int:transaction_id>')
@login_required
def view_transaction(transaction_id):
    """View transaction details"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check permissions
    if current_user.user_type != 'admin' and transaction.user_id != current_user.id:
        flash('You can only view your own transactions', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('transactions/view.html', transaction=transaction)

@transactions_bp.route('/<int:transaction_id>/return', methods=['GET', 'POST'])
@login_required
def return_book(transaction_id):
    """Return an issued book"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if book is already returned
    if transaction.status == 'returned':
        flash('This book has already been returned', 'warning')
        return redirect(url_for('transactions.view_transaction', transaction_id=transaction_id))
    
    if request.method == 'POST':
        # Update transaction
        transaction.return_date = datetime.utcnow()
        transaction.status = 'returned'
        
        # Update book availability
        book = Book.query.get(transaction.book_id)
        book.available_copies += 1
        
        # Calculate fine if overdue
        if transaction.is_overdue():
            days_late = transaction.days_overdue()
            fine_rate = 1.0  # $1 per day (can be made configurable)
            total_fine = days_late * fine_rate
            
            # Create fine record
            fine = Fine(
                transaction_id=transaction.id,
                amount=fine_rate,
                per_day_rate=fine_rate,
                days_late=days_late,
                total_amount=total_fine,
                status='unpaid'
            )
            
            db.session.add(fine)
            flash(f'Book returned successfully. Fine of ₹{total_fine:.2f} applied for {days_late} days late.', 'warning')
        else:
            flash('Book returned successfully', 'success')
        
        db.session.commit()
        return redirect(url_for('transactions.view_transaction', transaction_id=transaction_id))
    
    return render_template('transactions/return.html', transaction=transaction)

@transactions_bp.route('/<int:transaction_id>/renew', methods=['GET', 'POST'])
@login_required
def renew_book(transaction_id):
    """Renew an issued book"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if book is already returned
    if transaction.status == 'returned':
        flash('This book has already been returned', 'warning')
        return redirect(url_for('transactions.view_transaction', transaction_id=transaction_id))
    
    # Check permissions
    if current_user.user_type != 'admin' and transaction.user_id != current_user.id:
        flash('You can only renew your own transactions', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        additional_days = request.form.get('additional_days', type=int)
        
        # Validation
        if not additional_days or additional_days <= 0:
            flash('Please enter valid number of days', 'danger')
            return render_template('transactions/renew.html', transaction=transaction)
        
        # Update due date
        old_due_date = transaction.due_date
        transaction.due_date = transaction.due_date + timedelta(days=additional_days)
        
        db.session.commit()
        
        flash(f'Book renewed successfully. New due date: {transaction.due_date.strftime("%Y-%m-%d")}', 'success')
        return redirect(url_for('transactions.view_transaction', transaction_id=transaction_id))
    
    return render_template('transactions/renew.html', transaction=transaction)

@transactions_bp.route('/overdue')
@login_required
def overdue_books():
    """Display list of overdue books"""
    # Get overdue transactions
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'issued',
        Transaction.due_date < datetime.utcnow()
    ).order_by(Transaction.due_date).all()
    
    # Update status to overdue
    for transaction in overdue_transactions:
        if transaction.status != 'overdue':
            transaction.status = 'overdue'
    
    db.session.commit()
    
    return render_template('transactions/overdue.html', transactions=overdue_transactions)

@transactions_bp.route('/search_books')
@login_required
def search_books():
    """AJAX search for available books"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    books = Book.query.filter(
        Book.is_active == True,
        Book.available_copies > 0,
        Book.title.contains(query) | Book.author.contains(query) | Book.isbn.contains(query)
    ).limit(10).all()
    
    results = []
    for book in books:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'available_copies': book.available_copies
        })
    
    return jsonify(results)

@transactions_bp.route('/search_users')
@login_required
def search_users():
    """AJAX search for users (admin only)"""
    if current_user.user_type != 'admin':
        return jsonify([])
    
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        User.is_active == True,
        User.full_name.contains(query) | User.username.contains(query) | User.email.contains(query)
    ).limit(10).all()
    
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type
        })
    
    return jsonify(results)
