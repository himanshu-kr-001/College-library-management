"""
Book Management Routes
Handles CRUD operations for books
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.models import db, Book, Transaction
from datetime import datetime

books_bp = Blueprint('books', __name__)

@books_bp.route('/')
@login_required
def list_books():
    """Display list of all books"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    # Build query
    query = Book.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            Book.title.contains(search) |
            Book.author.contains(search) |
            Book.isbn.contains(search)
        )
    
    if category:
        query = query.filter_by(category=category)
    
    # Pagination
    books = query.order_by(Book.title).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get categories for filter dropdown
    categories = db.session.query(Book.category).filter(Book.category != '').distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('books/list.html', 
                         books=books, 
                         search=search, 
                         category=category,
                         categories=categories)

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    """Add a new book (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can add books', 'danger')
        return redirect(url_for('books.list_books'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        publication_year = request.form.get('publication_year')
        category = request.form.get('category')
        description = request.form.get('description')
        total_copies = request.form.get('total_copies', type=int)
        location = request.form.get('location')
        
        # Validation
        if not title or not author or not isbn:
            flash('Title, Author, and ISBN are required', 'danger')
            return render_template('books/add.html')
        
        # Check if ISBN already exists
        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash('A book with this ISBN already exists', 'danger')
            return render_template('books/add.html')
        
        # Create new book
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            publication_year=publication_year if publication_year else None,
            category=category,
            description=description,
            total_copies=total_copies if total_copies else 1,
            available_copies=total_copies if total_copies else 1,
            location=location
        )
        
        db.session.add(book)
        db.session.commit()
        
        flash(f'Book "{title}" added successfully', 'success')
        return redirect(url_for('books.list_books'))
    
    return render_template('books/add.html')

@books_bp.route('/<int:book_id>')
@login_required
def view_book(book_id):
    """View book details"""
    book = Book.query.get_or_404(book_id)
    
    # Get transaction history for this book
    transactions = Transaction.query.filter_by(book_id=book_id).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()
    
    return render_template('books/view.html', book=book, transactions=transactions)

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    """Edit book details (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can edit books', 'danger')
        return redirect(url_for('books.view_book', book_id=book_id))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        publication_year = request.form.get('publication_year')
        category = request.form.get('category')
        description = request.form.get('description')
        total_copies = request.form.get('total_copies', type=int)
        location = request.form.get('location')
        
        # Validation
        if not title or not author or not isbn:
            flash('Title, Author, and ISBN are required', 'danger')
            return render_template('books/edit.html', book=book)
        
        # Check if ISBN already exists (excluding current book)
        existing_book = Book.query.filter(Book.isbn == isbn, Book.id != book_id).first()
        if existing_book:
            flash('A book with this ISBN already exists', 'danger')
            return render_template('books/edit.html', book=book)
        
        # Update book
        old_total = book.total_copies
        book.title = title
        book.author = author
        book.isbn = isbn
        book.publisher = publisher
        book.publication_year = publication_year if publication_year else None
        book.category = category
        book.description = description
        book.total_copies = total_copies if total_copies else 1
        book.location = location
        
        # Update available copies if total increased
        if total_copies > old_total:
            book.available_copies += (total_copies - old_total)
        elif total_copies < old_total:
            # Don't let available copies exceed total
            issued_copies = old_total - book.available_copies
            book.available_copies = max(0, total_copies - issued_copies)
        
        db.session.commit()
        
        flash(f'Book "{title}" updated successfully', 'success')
        return redirect(url_for('books.view_book', book_id=book_id))
    
    return render_template('books/edit.html', book=book)

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    """Delete book (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can delete books', 'danger')
        return redirect(url_for('books.view_book', book_id=book_id))
    
    book = Book.query.get_or_404(book_id)
    
    # Check if book has any active transactions
    active_transactions = Transaction.query.filter_by(
        book_id=book_id, status='issued'
    ).count()
    
    if active_transactions > 0:
        flash('Cannot delete book with active transactions', 'danger')
        return redirect(url_for('books.view_book', book_id=book_id))
    
    # Soft delete (mark as inactive)
    book.is_active = False
    db.session.commit()
    
    flash(f'Book "{book.title}" deleted successfully', 'success')
    return redirect(url_for('books.list_books'))

@books_bp.route('/search')
@login_required
def search_books():
    """AJAX search for books"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    books = Book.query.filter(
        Book.is_active == True,
        Book.title.contains(query) | Book.author.contains(query) | Book.isbn.contains(query)
    ).limit(10).all()
    
    results = []
    for book in books:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'available': book.available_copies > 0
        })
    
    return jsonify(results)
