# Makefile for CampManager API
# Provides convenient commands for development, testing, and deployment

.PHONY: help install test test-unit test-integration test-auth test-coverage clean lint format run dev migrate upgrade-db create-migration

# Default target
help:
	@echo "CampManager API - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install          Install dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-auth        Run authentication tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-fast        Run tests excluding slow ones"
	@echo "  test-verbose     Run tests with verbose output"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black"
	@echo "  check-format     Check code formatting"
	@echo ""
	@echo "Development:"
	@echo "  run              Run the application"
	@echo "  dev              Run in development mode"
	@echo "  shell            Open Flask shell"
	@echo ""
	@echo "Database:"
	@echo "  migrate          Run database migrations"
	@echo "  upgrade-db       Upgrade database to latest migration"
	@echo "  create-migration Create new migration"
	@echo "  reset-db         Reset database (WARNING: destroys data)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up temporary files"
	@echo "  docs             Generate documentation"
	@echo "  requirements     Update requirements.txt"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 isort mypy

# Testing
test:
	python run_tests.py

test-unit:
	python run_tests.py --type unit

test-integration:
	python run_tests.py --type integration

test-auth:
	python run_tests.py --type auth

test-coverage:
	python run_tests.py --coverage

test-fast:
	python run_tests.py --fast

test-verbose:
	python run_tests.py --verbose

# Alternative pytest commands (direct)
pytest:
	pytest tests/

pytest-unit:
	pytest -m unit tests/

pytest-integration:
	pytest -m integration tests/

pytest-auth:
	pytest -m auth tests/

pytest-coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=html tests/

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
	@echo "Running mypy..."
	mypy app/ --ignore-missing-imports

format:
	@echo "Formatting with black..."
	black app/ tests/ run_tests.py --line-length=100
	@echo "Sorting imports with isort..."
	isort app/ tests/ run_tests.py --profile black

check-format:
	@echo "Checking format with black..."
	black --check app/ tests/ run_tests.py --line-length=100
	@echo "Checking import order with isort..."
	isort --check-only app/ tests/ run_tests.py --profile black

# Development
run:
	python run.py

dev:
	export FLASK_ENV=development && python run.py

shell:
	export FLASK_ENV=development && flask shell

# Database
migrate:
	export FLASK_ENV=development && flask db migrate

upgrade-db:
	export FLASK_ENV=development && flask db upgrade

create-migration:
	@read -p "Enter migration message: " message; \
	export FLASK_ENV=development && flask db migrate -m "$$message"

reset-db:
	@echo "WARNING: This will destroy all data in the database!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -f campmanager-dev.db; \
		export FLASK_ENV=development && flask db upgrade; \
		echo "Database reset complete."; \
	else \
		echo "Database reset cancelled."; \
	fi

# Utilities
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "Cleanup complete."

docs:
	@echo "Generating API documentation..."
	@echo "Visit http://localhost:5000/docs after starting the server"

requirements:
	pip freeze > requirements.txt

# Docker commands (if using Docker)
docker-build:
	docker build -t campmanager-api .

docker-run:
	docker run -p 5000:5000 campmanager-api

docker-test:
	docker run campmanager-api python run_tests.py

# Production commands
prod-install:
	pip install -r requirements.txt --no-dev

prod-run:
	export FLASK_ENV=production && gunicorn -w 4 -b 0.0.0.0:5000 "app:create_production_app()"

# CI/CD helpers
ci-test:
	python run_tests.py --coverage --verbose

ci-lint:
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
	black --check app/ tests/ run_tests.py --line-length=100
	isort --check-only app/ tests/ run_tests.py --profile black

# Security
security-check:
	@echo "Running security checks..."
	pip install safety bandit
	safety check
	bandit -r app/ -f json

# Performance
profile:
	@echo "Running performance profiling..."
	python -m cProfile -o profile.stats run.py
	@echo "Profile saved to profile.stats"

# Backup
backup-db:
	@echo "Creating database backup..."
	cp campmanager-dev.db "campmanager-dev-backup-$(shell date +%Y%m%d_%H%M%S).db"
	@echo "Backup created."

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from env.example..."; \
		cp env.example .env; \
		echo "Please edit .env file with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi

# Complete setup for new developers
setup: setup-env install upgrade-db
	@echo ""
	@echo "Setup complete! You can now:"
	@echo "1. Edit .env file with your configuration"
	@echo "2. Run 'make dev' to start development server"
	@echo "3. Run 'make test' to run tests"
	@echo "4. Visit http://localhost:5000/docs for API documentation"

# Health check
health:
	@echo "Checking application health..."
	@curl -s http://localhost:5000/health | python -m json.tool || echo "Application not running or health check failed"

# Quick development workflow
quick-test: format lint test-fast
	@echo "Quick development checks complete!"

# Full CI workflow
ci: install ci-lint ci-test
	@echo "CI workflow complete!"

# Show test coverage in browser
show-coverage: test-coverage
	@if command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	else \
		echo "Coverage report generated in htmlcov/index.html"; \
	fi
