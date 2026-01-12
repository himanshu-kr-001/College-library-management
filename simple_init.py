"""
Simple Database Initialization Script
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_database():
    """Create the database and tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'library.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20) UNIQUE,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            user_type VARCHAR(20) DEFAULT 'student',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            isbn VARCHAR(20) UNIQUE NOT NULL,
            publisher VARCHAR(100),
            publication_year INTEGER,
            category VARCHAR(50),
            description TEXT,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            price REAL DEFAULT 0.0,
            location VARCHAR(50),
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    cursor.execute("PRAGMA table_info(books)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'price' not in columns:
        cursor.execute('ALTER TABLE books ADD COLUMN price REAL DEFAULT 0.0')
    
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if 'student_id' not in user_columns:
        cursor.execute('ALTER TABLE users ADD COLUMN student_id VARCHAR(20)')
        # Note: UNIQUE constraint cannot be added to existing table in SQLite
        # The uniqueness will be enforced at application level
    
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
    
    # Add default admin user
    cursor.execute("SELECT * FROM users WHERE username = 'hk866311@gmail.com'")
    if not cursor.fetchone():
        admin_password = generate_password_hash('Hacker@2004')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, user_type)
            VALUES (?, ?, ?, ?, ?)
        ''', ('hk866311@gmail.com', 'hk866311@gmail.com', admin_password, 'Library Administrator', 'admin'))
        print("Default admin user created: username=hk866311@gmail.com, password=Hacker@2004")
    
    # Add sample books
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        sample_books = [
            ('Python Programming', 'John Smith', '978-0-123456-78-9', 'Tech Books', 2020, 'Programming', 'Complete guide to Python programming', 3, 3, 'A1-101'),
            ('Data Structures and Algorithms', 'Jane Doe', '978-0-234567-89-0', 'Computer Science Press', 2019, 'Computer Science', 'Fundamental concepts of data structures', 2, 2, 'B2-205'),
            ('Web Development with Flask', 'Mike Johnson', '978-0-345678-90-1', 'Web Dev Books', 2021, 'Web Development', 'Learn Flask web framework', 1, 1, 'C3-301'),
            ('Introduction to Algorithms', 'Thomas Cormen', '978-0-262-03384-8', 'MIT Press', 2009, 'Computer Science', 'Comprehensive introduction to algorithms', 2, 2, 'A2-102'),
            ('Clean Code', 'Robert Martin', '978-0-13-235088-4', 'Prentice Hall', 2008, 'Programming', 'A handbook of agile software craftsmanship', 1, 1, 'B1-201'),
            ('The Pragmatic Programmer', 'Andrew Hunt', '978-0-20-161622-4', 'Addison-Wesley', 1999, 'Programming', 'From journeyman to master', 2, 2, 'C2-302'),
            ('Design Patterns', 'Erich Gamma', '978-0-201-63361-0', 'Addison-Wesley', 1994, 'Programming', 'Elements of reusable object-oriented software', 1, 1, 'A3-103'),
            ('Refactoring', 'Martin Fowler', '978-0-13-475759-9', 'Addison-Wesley', 2018, 'Programming', 'Improving the design of existing code', 1, 1, 'B3-303')
        ]
        
        cursor.executemany('''
            INSERT INTO books (title, author, isbn, publisher, publication_year, category, description, total_copies, available_copies, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_books)
        print("Sample books added successfully!")
    
    # Add sample student
    cursor.execute("SELECT * FROM users WHERE username = 'student1'")
    if not cursor.fetchone():
        student_password = generate_password_hash('student123')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, phone, address, user_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('student1', 'student1@college.edu', student_password, 'Alice Student', '123-456-7890', '123 College Street', 'student'))
        print("Sample student created: username=student1, password=student123")
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at: {db_path}")
    print("\nLogin Credentials:")
    print("Admin: username=hk866311@gmail.com, password=Hacker@2004")
    print("Student: username=student1, password=student123")

if __name__ == '__main__':
    create_database()
