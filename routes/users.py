"""
User Management Routes
Handles user registration, management, and profile operations
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models.models import db, User, Transaction
from datetime import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
def list_users():
    """Display list of all users (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can view users list', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    user_type = request.args.get('user_type', '')
    
    # Build query
    query = User.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            User.username.contains(search) |
            User.full_name.contains(search) |
            User.email.contains(search)
        )
    
    if user_type:
        query = query.filter_by(user_type=user_type)
    
    # Pagination
    users = query.order_by(User.full_name).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('users/list.html', 
                         users=users, 
                         search=search, 
                         user_type=user_type)

@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add a new user (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can add users', 'danger')
        return redirect(url_for('users.list_users'))
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        user_type = request.form.get('user_type', 'student')
        
        # Validation
        if not username or not email or not password or not full_name:
            flash('Username, Email, Password, and Full Name are required', 'danger')
            return render_template('users/add.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('users/add.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('users/add.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            address=address,
            user_type=user_type
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{full_name}" added successfully', 'success')
        return redirect(url_for('users.list_users'))
    
    return render_template('users/add.html')

@users_bp.route('/<int:user_id>')
@login_required
def view_user(user_id):
    """View user details"""
    # Users can only view their own profile unless they're admin
    if current_user.user_type != 'admin' and current_user.id != user_id:
        flash('You can only view your own profile', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Get transaction history for this user
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()
    
    # Calculate statistics
    total_transactions = Transaction.query.filter_by(user_id=user_id).count()
    active_transactions = Transaction.query.filter_by(user_id=user_id, status='issued').count()
    
    return render_template('users/view.html', 
                         user=user, 
                         transactions=transactions,
                         total_transactions=total_transactions,
                         active_transactions=active_transactions)

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user details"""
    # Users can only edit their own profile unless they're admin
    if current_user.user_type != 'admin' and current_user.id != user_id:
        flash('You can only edit your own profile', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Only admin can change user type
        user_type = request.form.get('user_type')
        if current_user.user_type == 'admin' and user_type:
            user.user_type = user_type
        
        # Validation
        if not email or not full_name:
            flash('Email and Full Name are required', 'danger')
            return render_template('users/edit.html', user=user)
        
        # Check if email already exists (excluding current user)
        existing_user = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_user:
            flash('Email already exists', 'danger')
            return render_template('users/edit.html', user=user)
        
        # Update user
        user.email = email
        user.full_name = full_name
        user.phone = phone
        user.address = address
        
        db.session.commit()
        
        flash(f'User profile updated successfully', 'success')
        
        if current_user.user_type == 'admin':
            return redirect(url_for('users.view_user', user_id=user_id))
        else:
            return redirect(url_for('auth.profile'))
    
    return render_template('users/edit.html', user=user)

@users_bp.route('/<int:user_id>/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    """Reset user password (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can reset passwords', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not new_password or not confirm_password:
            flash('Please fill all fields', 'danger')
            return render_template('users/reset_password.html', user=user)
        
        # Check passwords match
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('users/reset_password.html', user=user)
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash(f'Password for "{user.full_name}" reset successfully', 'success')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    return render_template('users/reset_password.html', user=user)

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user (admin only)"""
    if current_user.user_type != 'admin':
        flash('Only administrators can delete users', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting admin users or self
    if user.user_type == 'admin':
        flash('Cannot delete administrator users', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    # Check if user has active transactions
    active_transactions = Transaction.query.filter_by(
        user_id=user_id, status='issued'
    ).count()
    
    if active_transactions > 0:
        flash('Cannot delete user with active transactions', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    # Soft delete (mark as inactive)
    user.is_active = False
    db.session.commit()
    
    flash(f'User "{user.full_name}" deleted successfully', 'success')
    return redirect(url_for('users.list_users'))
