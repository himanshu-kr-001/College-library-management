"""
Database Models for Library Management System
This file contains all the database models using SQLAlchemy ORM
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    user_type = db.Column(db.String(20), nullable=False, default='student')  # 'admin' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    """Book model for library catalog"""
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    location = db.Column(db.String(50))  # Shelf/aisle location
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='book', lazy=True)
    
    def __repr__(self):
        return f'<Book {self.title}>'
    
    def is_available(self):
        """Check if book is available for issue"""
        return self.available_copies > 0 and self.is_active

class Transaction(db.Model):
    """Transaction model for book issue/return records"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='issued')  # 'issued', 'returned', 'overdue'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fine = db.relationship('Fine', backref='transaction', uselist=False)
    
    def __repr__(self):
        return f'<Transaction {self.id}>'
    
    def is_overdue(self):
        """Check if transaction is overdue"""
        if self.return_date:
            return False
        return datetime.utcnow() > self.due_date
    
    def days_overdue(self):
        """Calculate number of days overdue"""
        if not self.is_overdue():
            return 0
        today = datetime.utcnow()
        return (today - self.due_date).days

class Fine(db.Model):
    """Fine model for late return penalties"""
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    per_day_rate = db.Column(db.Float, nullable=False, default=1.0)  # Fine per day
    days_late = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='unpaid')  # 'unpaid', 'partially_paid', 'paid'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Fine {self.id}>'
    
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        return self.total_amount - self.paid_amount
    
    def is_fully_paid(self):
        """Check if fine is fully paid"""
        return self.paid_amount >= self.total_amount

# Database initialization helper functions
def init_database():
    """Initialize database with default admin user"""
    from werkzeug.security import generate_password_hash
    
    # Create all tables
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create default admin user
        admin = User(
            username='admin',
            email='admin@library.com',
            password_hash=generate_password_hash('admin123'),
            full_name='Library Administrator',
            user_type='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: username=admin, password=admin123")
    
    print("Database initialized successfully!")

def add_sample_data():
    """Add sample data for testing"""
    # Sample books
    sample_books = [
        Book(
            title="Python Programming",
            author="John Smith",
            isbn="978-0-123456-78-9",
            publisher="Tech Books",
            publication_year=2020,
            category="Programming",
            description="Complete guide to Python programming",
            total_copies=3,
            available_copies=3,
            location="A1-101"
        ),
        Book(
            title="Data Structures and Algorithms",
            author="Jane Doe",
            isbn="978-0-234567-89-0",
            publisher="Computer Science Press",
            publication_year=2019,
            category="Computer Science",
            description="Fundamental concepts of data structures",
            total_copies=2,
            available_copies=2,
            location="B2-205"
        ),
        Book(
            title="Web Development with Flask",
            author="Mike Johnson",
            isbn="978-0-345678-90-1",
            publisher="Web Dev Books",
            publication_year=2021,
            category="Web Development",
            description="Learn Flask web framework",
            total_copies=1,
            available_copies=1,
            location="C3-301"
        )
    ]
    
    # Sample student
    sample_student = User(
        username="student1",
        email="student1@college.edu",
        password_hash="pbkdf2:sha256:260000$salt$hash",  # Will be set properly
        full_name="Alice Student",
        phone="123-456-7890",
        address="123 College Street",
        user_type="student"
    )
    
    # Add sample data if not exists
    if not Book.query.first():
        for book in sample_books:
            db.session.add(book)
    
    if not User.query.filter_by(username='student1').first():
        from werkzeug.security import generate_password_hash
        sample_student.password_hash = generate_password_hash('student123')
        db.session.add(sample_student)
    
    db.session.commit()
    print("Sample data added successfully!")
