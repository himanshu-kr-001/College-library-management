"""
Database Initialization Script
Run this script to create and initialize the database
"""

import os
from models.models import db, init_database, add_sample_data

def main():
    """Main function to initialize database"""
    # Get the absolute path of the current directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Configure database
    db_uri = f'sqlite:///{os.path.join(basedir, "library.db")}'
    
    # Create Flask app context
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with app
    db.init_app(app)
    
    with app.app_context():
        print("Initializing database...")
        init_database()
        
        print("\nAdding sample data...")
        add_sample_data()
        
        print(f"\nDatabase created successfully at: {db_uri}")
        print("\nDefault Login Credentials:")
        print("Admin: username=admin, password=admin123")
        print("Student: username=student1, password=student123")

if __name__ == '__main__':
    main()
