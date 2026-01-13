"""
GitHub Pages Deployment Script
Converts Flask app to static HTML for GitHub Pages deployment
"""

import os
import shutil
from jinja2 import Environment, FileSystemLoader
import json

def create_static_site():
    """Create static version of the Flask app for GitHub Pages"""
    
    # Create static directory
    static_dir = 'docs'
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    os.makedirs(static_dir)
    
    # Copy static files
    if os.path.exists('static'):
        shutil.copytree('static', os.path.join(static_dir, 'static'))
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    
    # Create main index page (login page)
    create_login_page(env, static_dir)
    
    # Create dashboard page
    create_dashboard_page(env, static_dir)
    
    # Create additional pages
    create_additional_pages(env, static_dir)
    
    # Create 404 page
    create_404_page(env, static_dir)
    
    print(f"Static site created in '{static_dir}' directory")
    print("Ready for GitHub Pages deployment!")

def create_login_page(env, static_dir):
    """Create login page"""
    template = env.get_template('login.html')
    
    # Create a simplified version of login page for static deployment
    login_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Sityog Library Management</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        /* Glassmorphism Login Styles */
        :root {{
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --border-radius: 12px;
            --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        .login-container {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 2rem;
            gap: 3rem;
        }}

        .login-form-container {{
            flex: 0 0 auto;
            max-width: 420px;
            width: 100%;
            z-index: 10;
        }}

        .image-container {{
            flex: 1.2;
            display: flex;
            align-items: center;
            justify-content: center;
            max-width: 1000px;
            z-index: 5;
        }}

        .profile-image {{
            width: 100%;
            height: 100%;
            max-height: 95vh;
            object-fit: contain;
            border-radius: 25px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
            transition: transform 0.3s ease;
        }}

        .profile-image:hover {{
            transform: scale(1.05);
        }}

        .card-component {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px) saturate(1.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
            transition: var(--transition-smooth);
            overflow: hidden;
        }}

        .header-component {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }}

        .title-component {{
            color: white;
            font-weight: 700;
            text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
            margin: 0;
            font-size: 1.5rem;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}

        .form-component {{
            padding: 2rem;
        }}

        .input-group-component {{
            margin-bottom: 1.5rem;
            position: relative;
        }}

        .input-label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #343a40;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .input-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #e0e0e0;
            border-radius: var(--border-radius);
            transition: var(--transition-smooth);
            overflow: hidden;
        }}

        .input-wrapper:focus-within {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }}

        .input-icon {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #e0e0e0;
            border-radius: var(--border-radius) 0 0 0 var(--border-radius);
            padding: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary-color);
            font-size: 1.1rem;
        }}

        .input-field {{
            flex: 1;
            border: none;
            background: transparent;
            padding: 1rem;
            font-size: 1rem;
            outline: none;
            transition: var(--transition-smooth);
        }}

        .button-component {{
            width: 100%;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
            border-radius: var(--border-radius);
            padding: 1rem 2rem;
            font-weight: 600;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
            color: white;
            cursor: pointer;
            transition: var(--transition-smooth);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}

        .button-component:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
            color: white;
        }}

        .footer-component {{
            background: rgba(248, 249, 250, 0.8);
            border-radius: 0 0 var(--border-radius) var(--border-radius);
            border-top: 1px solid rgba(102, 126, 234, 0.1);
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(5px);
        }}

        @media (max-width: 768px) {{
            .login-container {{
                flex-direction: column;
                padding: 1rem;
                gap: 2rem;
            }}

            .login-form-container {{
                max-width: 100%;
                order: 2;
            }}

            .image-container {{
                flex: 1;
                max-width: 100%;
                order: 1;
                margin-bottom: 1rem;
            }}

            .profile-image {{
                max-height: 50vh;
                border-radius: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <!-- Left Side - Login Form -->
        <div class="login-form-container">
            <div class="card-component">
                <!-- Header Component -->
                <div class="header-component">
                    <div class="title-component">
                        <i class="fas fa-book"></i>
                        Sityog Library Login
                    </div>
                </div>
                
                <!-- Form Component -->
                <div class="form-component">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        This is a static demo version. For full functionality, please deploy to a server.
                    </div>
                    
                    <form id="demoForm">
                        <!-- Username Input Component -->
                        <div class="input-group-component">
                            <label for="username" class="input-label">Username</label>
                            <div class="input-wrapper">
                                <div class="input-icon">
                                    <i class="fas fa-user"></i>
                                </div>
                                <input type="text" 
                                       class="input-field" 
                                       id="username" 
                                       name="username" 
                                       placeholder="hk866311@gmail.com" 
                                       value="hk866311@gmail.com"
                                       readonly>
                            </div>
                        </div>
                        
                        <!-- Password Input Component -->
                        <div class="input-group-component">
                            <label for="password" class="input-label">Password</label>
                            <div class="input-wrapper">
                                <div class="input-icon">
                                    <i class="fas fa-lock"></i>
                                </div>
                                <input type="password" 
                                       class="input-field" 
                                       id="password" 
                                       name="password" 
                                       placeholder="Enter password" 
                                       value="Hacker@2004"
                                       readonly>
                            </div>
                        </div>
                        
                        <!-- Submit Button Component -->
                        <div class="mb-3">
                            <button type="button" class="button-component" onclick="showDashboard()">
                                <i class="fas fa-sign-in-alt me-2"></i>
                                View Dashboard Demo
                            </button>
                        </div>
                    </form>
                </div>
                
                <!-- Footer Component -->
                <div class="footer-component">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Demo: hk866311@gmail.com / Hacker@2004
                    </small>
                </div>
            </div>
        </div>
        
        <!-- Right Side - Profile Image -->
        <div class="image-container">
            <img src="static/images/sityog-banner-2.jpg" 
                 alt="Sityog Library" 
                 class="profile-image">
        </div>
    </div>

    <script>
        function showDashboard() {{
            window.location.href = 'dashboard.html';
        }}
    </script>
</body>
</html>
"""
    
    with open(os.path.join(static_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(login_html)

def create_dashboard_page(env, static_dir):
    """Create dashboard page"""
    dashboard_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Sityog Library Management</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .dashboard-container {{
            padding: 2rem;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 1rem;
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        
        .nav-link {{
            color: #667eea;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .nav-link:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: #764ba2;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white mb-4">
        <div class="container">
            <a class="navbar-brand" href="index.html">
                <i class="fas fa-book me-2"></i>
                Sityog Library
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="index.html">
                    <i class="fas fa-sign-out-alt me-1"></i>
                    Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container dashboard-container">
        <div class="row">
            <div class="col-12">
                <h1><i class="fas fa-tachometer-alt me-2"></i>Dashboard</h1>
                <p class="text-muted">Welcome back, Library Administrator!</p>
            </div>
        </div>

        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <div class="stat-icon text-primary">
                        <i class="fas fa-book"></i>
                    </div>
                    <div class="stat-number">8</div>
                    <div class="text-muted">Total Books</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <div class="stat-icon text-success">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-number">2</div>
                    <div class="text-muted">Total Users</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <div class="stat-icon text-warning">
                        <i class="fas fa-book-open"></i>
                    </div>
                    <div class="stat-number">0</div>
                    <div class="text-muted">Issued Books</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <div class="stat-icon text-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="stat-number">0</div>
                    <div class="text-muted">Overdue Books</div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="row">
            <div class="col-12">
                <div class="stat-card">
                    <h3><i class="fas fa-cogs me-2"></i>Quick Actions</h3>
                    <div class="row mt-3">
                        <div class="col-md-3 mb-3">
                            <div class="text-center">
                                <i class="fas fa-plus-circle fa-3x text-primary mb-2"></i>
                                <h5>Add Book</h5>
                                <p class="text-muted">Add new books to library</p>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="text-center">
                                <i class="fas fa-user-plus fa-3x text-success mb-2"></i>
                                <h5>Add Student</h5>
                                <p class="text-muted">Register new students</p>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="text-center">
                                <i class="fas fa-exchange-alt fa-3x text-warning mb-2"></i>
                                <h5>Issue Book</h5>
                                <p class="text-muted">Issue books to students</p>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="text-center">
                                <i class="fas fa-undo fa-3x text-info mb-2"></i>
                                <h5>Return Book</h5>
                                <p class="text-muted">Process book returns</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Demo Notice -->
        <div class="row">
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Demo Mode:</strong> This is a static demonstration. For full functionality including database operations, please deploy the Flask application to a server like Render, Heroku, or Vercel.
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    with open(os.path.join(static_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard_html)

def create_additional_pages(env, static_dir):
    """Create additional pages for demo"""
    pages = [
        ('books.html', 'Books Management', 'Manage library books'),
        ('students.html', 'Students Management', 'Manage student records'),
        ('transactions.html', 'Transactions', 'View issue/return history'),
    ]
    
    for page_name, title, description in pages:
        page_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Sityog Library Management</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .page-container {{
            padding: 2rem;
        }}
        
        .content-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        
        .nav-link {{
            color: #667eea;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .nav-link:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: #764ba2;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white mb-4">
        <div class="container">
            <a class="navbar-brand" href="index.html">
                <i class="fas fa-book me-2"></i>
                Sityog Library
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="dashboard.html">
                    <i class="fas fa-tachometer-alt me-1"></i>
                    Dashboard
                </a>
                <a class="nav-link" href="index.html">
                    <i class="fas fa-sign-out-alt me-1"></i>
                    Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container page-container">
        <div class="row">
            <div class="col-12">
                <div class="content-card">
                    <h1><i class="fas fa-cog me-2"></i>{title}</h1>
                    <p class="text-muted mb-4">{description}</p>
                    
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Static Demo:</strong> This page shows the layout and design. For full functionality including database operations, please deploy the Flask application to a server.
                    </div>
                    
                    <div class="text-center mt-4">
                        <i class="fas fa-tools fa-4x text-muted mb-3"></i>
                        <h3>Under Development</h3>
                        <p class="text-muted">Full functionality available in server deployment</p>
                        <a href="dashboard.html" class="btn btn-primary">
                            <i class="fas fa-arrow-left me-2"></i>
                            Back to Dashboard
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        
        with open(os.path.join(static_dir, page_name), 'w', encoding='utf-8') as f:
            f.write(page_html)

def create_404_page(env, static_dir):
    """Create 404 error page"""
    not_found_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found - Sityog Library</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .error-container {{
            text-align: center;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .error-code {{
            font-size: 6rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 1rem;
        }}
        
        .error-message {{
            font-size: 1.5rem;
            color: #666;
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">404</div>
        <div class="error-message">Page Not Found</div>
        <p class="text-muted mb-4">The page you're looking for doesn't exist.</p>
        <a href="index.html" class="btn btn-primary btn-lg">
            <i class="fas fa-home me-2"></i>
            Go Home
        </a>
    </div>
</body>
</html>
"""
    
    with open(os.path.join(static_dir, '404.html'), 'w', encoding='utf-8') as f:
        f.write(not_found_html)

if __name__ == '__main__':
    create_static_site()
