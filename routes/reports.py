"""
Reports Routes
Handles various reports for library management
"""

from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.models import db, Book, Transaction, Fine, User
import csv
from io import StringIO

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def dashboard():
    """Reports dashboard"""
    return render_template('reports/dashboard.html')

@reports_bp.route('/issued_books')
@login_required
def issued_books():
    """Report of currently issued books"""
    # Get issued transactions
    transactions = Transaction.query.filter_by(status='issued').order_by(
        Transaction.issue_date.desc()
    ).all()
    
    # Statistics
    total_issued = len(transactions)
    overdue_count = Transaction.query.filter_by(status='overdue').count()
    
    return render_template('reports/issued_books.html', 
                         transactions=transactions,
                         total_issued=total_issued,
                         overdue_count=overdue_count)

@reports_bp.route('/available_books')
@login_required
def available_books():
    """Report of available books"""
    # Get available books
    books = Book.query.filter_by(is_active=True).filter(
        Book.available_copies > 0
    ).order_by(Book.title).all()
    
    # Statistics
    total_available = len(books)
    low_stock = [book for book in books if book.available_copies <= 1]
    
    return render_template('reports/available_books.html',
                         books=books,
                         total_available=total_available,
                         low_stock=low_stock)

@reports_bp.route('/overdue_books')
@login_required
def overdue_books_report():
    """Report of overdue books"""
    # Get overdue transactions
    overdue_transactions = Transaction.query.filter(
        Transaction.status.in_(['issued', 'overdue']),
        Transaction.due_date < datetime.utcnow()
    ).order_by(Transaction.due_date).all()
    
    # Calculate statistics
    total_overdue = len(overdue_transactions)
    total_fines = sum(t.days_overdue() for t in overdue_transactions)
    
    return render_template('reports/overdue_books.html',
                         transactions=overdue_transactions,
                         total_overdue=total_overdue,
                         total_fines=total_fines)

@reports_bp.route('/fines')
@login_required
def fines_report():
    """Report of fines"""
    # Get fines
    fines = Fine.query.order_by(Fine.created_at.desc()).all()
    
    # Statistics
    total_fines = len(fines)
    unpaid_fines = Fine.query.filter_by(status='unpaid').count()
    total_amount = sum(f.total_amount for f in fines)
    unpaid_amount = sum(f.remaining_amount() for f in fines if f.status == 'unpaid')
    
    return render_template('reports/fines.html',
                         fines=fines,
                         total_fines=total_fines,
                         unpaid_fines=unpaid_fines,
                         total_amount=total_amount,
                         unpaid_amount=unpaid_amount)

@reports_bp.route('/user_activity')
@login_required
def user_activity():
    """Report of user activity"""
    # Get users with their transaction counts
    users = User.query.filter_by(is_active=True).all()
    
    user_stats = []
    for user in users:
        total_transactions = Transaction.query.filter_by(user_id=user.id).count()
        active_transactions = Transaction.query.filter_by(
            user_id=user.id, status='issued'
        ).count()
        overdue_transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.status.in_(['issued', 'overdue']),
            Transaction.due_date < datetime.utcnow()
        ).count()
        
        user_stats.append({
            'user': user,
            'total_transactions': total_transactions,
            'active_transactions': active_transactions,
            'overdue_transactions': overdue_transactions
        })
    
    # Sort by total transactions
    user_stats.sort(key=lambda x: x['total_transactions'], reverse=True)
    
    return render_template('reports/user_activity.html', user_stats=user_stats)

@reports_bp.route('/book_statistics')
@login_required
def book_statistics():
    """Report of book statistics"""
    # Get all books
    books = Book.query.filter_by(is_active=True).all()
    
    book_stats = []
    for book in books:
        total_transactions = Transaction.query.filter_by(book_id=book.id).count()
        current_issues = Transaction.query.filter_by(
            book_id=book.id, status='issued'
        ).count()
        
        book_stats.append({
            'book': book,
            'total_transactions': total_transactions,
            'current_issues': current_issues,
            'popularity': total_transactions
        })
    
    # Sort by popularity
    book_stats.sort(key=lambda x: x['popularity'], reverse=True)
    
    # Category statistics
    categories = db.session.query(Book.category).filter(Book.category != '').distinct().all()
    category_stats = []
    
    for category in categories:
        cat_name = category[0]
        books_in_category = Book.query.filter_by(category=cat_name, is_active=True).all()
        total_books = len(books_in_category)
        total_transactions = sum(
            Transaction.query.filter_by(book_id=book.id).count()
            for book in books_in_category
        )
        
        category_stats.append({
            'category': cat_name,
            'total_books': total_books,
            'total_transactions': total_transactions
        })
    
    category_stats.sort(key=lambda x: x['total_transactions'], reverse=True)
    
    return render_template('reports/book_statistics.html',
                         book_stats=book_stats,
                         category_stats=category_stats)

@reports_bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Export report to CSV"""
    
    if report_type == 'issued_books':
        transactions = Transaction.query.filter_by(status='issued').all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Transaction ID', 'User', 'Book Title', 'Author', 
                        'Issue Date', 'Due Date', 'Days Overdue'])
        
        # Data
        for t in transactions:
            writer.writerow([
                t.id,
                t.user.full_name,
                t.book.title,
                t.book.author,
                t.issue_date.strftime('%Y-%m-%d'),
                t.due_date.strftime('%Y-%m-%d'),
                t.days_overdue()
            ])
        
        filename = f'issued_books_{datetime.now().strftime("%Y%m%d")}.csv'
        
    elif report_type == 'overdue_books':
        transactions = Transaction.query.filter(
            Transaction.status.in_(['issued', 'overdue']),
            Transaction.due_date < datetime.utcnow()
        ).all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Transaction ID', 'User', 'Book Title', 'Author',
                        'Issue Date', 'Due Date', 'Days Overdue', 'Fine Amount'])
        
        # Data
        for t in transactions:
            days_overdue = t.days_overdue()
            fine_amount = days_overdue * 1.0  # $1 per day
            
            writer.writerow([
                t.id,
                t.user.full_name,
                t.book.title,
                t.book.author,
                t.issue_date.strftime('%Y-%m-%d'),
                t.due_date.strftime('%Y-%m-%d'),
                days_overdue,
                f'₹{fine_amount:.2f}'
            ])
        
        filename = f'overdue_books_{datetime.now().strftime("%Y%m%d")}.csv'
        
    elif report_type == 'fines':
        fines = Fine.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Fine ID', 'User', 'Book Title', 'Days Late',
                        'Total Amount', 'Paid Amount', 'Status'])
        
        # Data
        for fine in fines:
            writer.writerow([
                fine.id,
                fine.transaction.user.full_name,
                fine.transaction.book.title,
                fine.days_late,
                f'₹{fine.total_amount:.2f}',
                f'₹{fine.paid_amount:.2f}',
                fine.status
            ])
        
        filename = f'fines_{datetime.now().strftime("%Y%m%d")}.csv'
        
    else:
        flash('Invalid report type', 'danger')
        return redirect(url_for('reports.dashboard'))
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@reports_bp.route('/daily_summary')
@login_required
def daily_summary():
    """Daily summary report"""
    # Get today's date
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Today's statistics
    books_issued_today = Transaction.query.filter(
        Transaction.issue_date >= today_start,
        Transaction.issue_date <= today_end
    ).count()
    
    books_returned_today = Transaction.query.filter(
        Transaction.return_date >= today_start,
        Transaction.return_date <= today_end
    ).count()
    
    new_users_today = User.query.filter(
        User.created_at >= today_start,
        User.created_at <= today_end
    ).count()
    
    fines_created_today = Fine.query.filter(
        Fine.created_at >= today_start,
        Fine.created_at <= today_end
    ).count()
    
    # Recent activity
    recent_transactions = Transaction.query.filter(
        Transaction.created_at >= today_start
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    return render_template('reports/daily_summary.html',
                         books_issued_today=books_issued_today,
                         books_returned_today=books_returned_today,
                         new_users_today=new_users_today,
                         fines_created_today=fines_created_today,
                         recent_transactions=recent_transactions,
                         today=today)
