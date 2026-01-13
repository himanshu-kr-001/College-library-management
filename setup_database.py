"""
Database initialization script for Render deployment
This script will be executed once during deployment
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

def create_database():
    """Create database and tables"""
    # Use /tmp directory for Render
    db_path = os.environ.get('DATABASE_PATH', '/tmp/library.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            user_type VARCHAR(20) DEFAULT 'student',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            isbn VARCHAR(20) UNIQUE,
            publisher VARCHAR(100),
            publication_year INTEGER,
            category VARCHAR(50),
            description TEXT,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            location VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            due_date DATETIME NOT NULL,
            return_date DATETIME,
            status VARCHAR(20) DEFAULT 'issued',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    # Create fines table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            amount REAL DEFAULT 0.0,
            per_day_rate REAL DEFAULT 1.0,
            days_late INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0.0,
            paid_amount REAL DEFAULT 0.0,
            status VARCHAR(20) DEFAULT 'unpaid',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            paid_date DATETIME,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id)
        )
    ''')
    
    conn.commit()
    
    # Add admin user
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@library.com')
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
    if not cursor.fetchone():
        admin_password_hash = generate_password_hash(admin_password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, user_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_username, admin_email, admin_password_hash, 'Library Administrator', 'admin'))
        print(f"Admin user created: username={admin_username}")
    
    # Add sample books
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        sample_books = [
            ('Python Programming', 'John Smith', '978-0-123456-78-9', 'Tech Books', 2020, 'Programming', 'Complete guide to Python programming', 3, 3, 'A1-101'),
            ('Data Structures and Algorithms', 'Jane Doe', '978-0-234567-89-0', 'Computer Science Press', 2019, 'Computer Science', 'Fundamental concepts of data structures', 2, 2, 'B2-205'),
            ('Web Development with Flask', 'Mike Johnson', '978-0-345678-90-1', 'Web Dev Books', 2021, 'Web Development', 'Learn Flask web framework', 1, 1, 'C3-301'),
        ]
        
        cursor.executemany('''
            INSERT INTO books (title, author, isbn, publisher, publication_year, category, description, total_copies, available_copies, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_books)
        print("Sample books added")
    
    conn.close()
    print(f"Database created successfully at: {db_path}")

if __name__ == '__main__':
    create_database()
