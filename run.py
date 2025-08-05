#!/usr/bin/env python3
"""
CampManager API - Application Entry Point

This is the main entry point for running the CampManager API application.
It creates the Flask app instance and runs it with appropriate configuration.
"""

import os
import sys
from flask.cli import FlaskGroup

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db


# Create application instance
app = create_app()

# Create Flask CLI group for management commands
cli = FlaskGroup(app)


@cli.command()
def deploy():
    """Run deployment tasks"""
    print("Starting deployment tasks...")
    
    # Create database tables
    db.create_all()
    print("✓ Database tables created")
    
    # Create uploads directory
    upload_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"✓ Upload directory created: {upload_dir}")
    
    print("Deployment completed successfully!")


@cli.command()
def test():
    """Run tests"""
    import unittest
    
    # Discover and run tests
    tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command()
def coverage():
    """Run tests with coverage report"""
    try:
        import coverage
    except ImportError:
        print("Coverage package not installed. Install with: pip install coverage")
        sys.exit(1)
    
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    import unittest
    tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    
    cov.stop()
    cov.save()
    
    # Generate coverage report
    print("\nCoverage Report:")
    cov.report()
    
    # Generate HTML coverage report
    cov.html_report(directory='htmlcov')
    print("\nHTML coverage report generated in 'htmlcov' directory")
    
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command()
def lint():
    """Run code linting"""
    try:
        import flake8.api.legacy as flake8
    except ImportError:
        print("Flake8 not installed. Install with: pip install flake8")
        sys.exit(1)
    
    style_guide = flake8.get_style_guide(
        exclude=['migrations', 'venv', '__pycache__'],
        max_line_length=100
    )
    
    report = style_guide.check_files(['.'])
    
    if report.get_count() == 0:
        print("✓ No linting errors found")
        sys.exit(0)
    else:
        print(f"✗ Found {report.get_count()} linting errors")
        sys.exit(1)


@cli.command()
def format_code():
    """Format code using black"""
    try:
        import black
    except ImportError:
        print("Black not installed. Install with: pip install black")
        sys.exit(1)
    
    import subprocess
    
    # Format Python files
    result = subprocess.run([
        sys.executable, '-m', 'black', 
        '--line-length', '100',
        '--exclude', 'migrations',
        '.'
    ])
    
    if result.returncode == 0:
        print("✓ Code formatted successfully")
    else:
        print("✗ Code formatting failed")
        sys.exit(1)


@cli.command()
def seed_db():
    """Seed database with sample data"""
    from app.user.models import User
    from app.camp.models import Camp, Church, Category
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    print("Seeding database with sample data...")
    
    # Create sample camp manager
    manager = User.query.filter_by(email='manager@example.com').first()
    if not manager:
        manager = User(
            email='manager@example.com',
            full_name='John Manager',
            role='camp_manager'
        )
        manager.set_password('password123')
        db.session.add(manager)
        db.session.commit()
        print("✓ Sample camp manager created")
    
    # Create sample camp
    camp = Camp.query.filter_by(name='Summer Camp 2024').first()
    if not camp:
        camp = Camp(
            name='Summer Camp 2024',
            start_date=datetime.now().date() + timedelta(days=30),
            end_date=datetime.now().date() + timedelta(days=37),
            location='Camp Grounds, Accra',
            base_fee=Decimal('250.00'),
            capacity=100,
            description='Annual summer camp for youth',
            registration_deadline=datetime.now() + timedelta(days=20),
            camp_manager_id=manager.id
        )
        db.session.add(camp)
        db.session.commit()
        print("✓ Sample camp created")
        
        # Create sample churches
        churches = [
            Church(name='Central Baptist Church', camp_id=camp.id),
            Church(name='Grace Methodist Church', camp_id=camp.id),
            Church(name='Unity Presbyterian Church', camp_id=camp.id)
        ]
        
        for church in churches:
            db.session.add(church)
        
        # Create sample categories
        categories = [
            Category(
                name='Regular',
                discount_percentage=Decimal('0'),
                camp_id=camp.id,
                is_default=True
            ),
            Category(
                name='Early Bird',
                discount_percentage=Decimal('15'),
                camp_id=camp.id
            ),
            Category(
                name='Campus Leader',
                discount_percentage=Decimal('25'),
                camp_id=camp.id
            )
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()
        print("✓ Sample churches and categories created")
    
    print("Database seeding completed!")


@cli.command()
def routes():
    """Display all application routes"""
    from flask import url_for
    
    print("Application Routes:")
    print("=" * 50)
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': rule.rule
        })
    
    # Sort routes by path
    routes.sort(key=lambda x: x['path'])
    
    # Print routes in a formatted table
    for route in routes:
        print(f"{route['methods']:<15} {route['path']:<40} {route['endpoint']}")


if __name__ == '__main__':
    # Get environment variables
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Print startup information
    print("=" * 60)
    print("🏕️  CampManager API Starting...")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print("=" * 60)

    
    if len(sys.argv) > 1:
        # Run CLI commands
        cli()
    else:
        # Run the development server
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=True
        )

        