"""
Main Flask Application for Library Management System
This is the entry point of the application for Render deployment
"""

import os
from simple_app import app

# Configure for Render deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
