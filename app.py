"""
Main Flask Application for Library Management System
This is the entry point of the application
"""

from simple_app import app


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
