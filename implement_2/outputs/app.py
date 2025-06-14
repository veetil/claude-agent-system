#!/usr/bin/env python3
"""
Claude Agent Demo - Production-ready Flask Web Application
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates/templates')

# Load configuration
CONFIG_PATH = Path(__file__).parent / 'config' / 'app_config.json'
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        app.config.update(config)
        logger.info(f"Configuration loaded from {CONFIG_PATH}")
except FileNotFoundError:
    logger.error(f"Configuration file not found at {CONFIG_PATH}")
    config = {
        "app_name": "Claude Agent Demo",
        "version": "1.0.0",
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
        "features": {
            "api_enabled": True,
            "rate_limiting": True,
            "cors_enabled": True
        }
    }
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in configuration file: {e}")
    raise

# Initialize extensions
if config.get('features', {}).get('cors_enabled', True):
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logger.info("CORS enabled")

if config.get('features', {}).get('rate_limiting', True):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    logger.info("Rate limiting enabled")

# Database initialization
def init_db():
    """Initialize the SQLite database."""
    db_config = config.get('database', {})
    if db_config.get('type') == 'sqlite':
        db_path = db_config.get('path', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                response_time_ms INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {db_path}")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('index.html', 
                         app_name=config['app_name'],
                         version=config['version']), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('index.html', 
                         app_name=config['app_name'],
                         version=config['version']), 500

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Handle HTTP exceptions."""
    if request.path.startswith('/api/'):
        return jsonify({'error': e.description}), e.code
    return e

# Middleware
@app.before_request
def before_request():
    """Log incoming requests."""
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    """Log response status."""
    logger.info(f"Response: {response.status}")
    return response

# Helper functions
def require_api_enabled(f):
    """Decorator to check if API is enabled."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.get('features', {}).get('api_enabled', True):
            return jsonify({'error': 'API is disabled'}), 503
        return f(*args, **kwargs)
    return decorated_function

def get_public_config() -> Dict[str, Any]:
    """Get public configuration (excludes sensitive data)."""
    return {
        'app_name': config.get('app_name'),
        'version': config.get('version'),
        'features': config.get('features', {})
    }

# Routes
@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html', 
                         app_name=config['app_name'],
                         version=config['version'])

@app.route('/api')
def api_docs():
    """Render the API documentation page."""
    return render_template('api.html',
                         app_name=config['app_name'])

@app.route('/status')
def status_page():
    """Render a status page."""
    # For now, redirect to API status
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'app_name': config['app_name'],
        'version': config['version']
    })

# API Routes
@app.route('/api/status', methods=['GET'])
@require_api_enabled
def api_status():
    """Get system status."""
    try:
        # Check database connection
        db_status = 'ok'
        if config.get('database', {}).get('type') == 'sqlite':
            try:
                conn = sqlite3.connect(config['database']['path'])
                conn.execute('SELECT 1')
                conn.close()
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                db_status = 'error'
        
        return jsonify({
            'status': 'ok' if db_status == 'ok' else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'api': 'ok',
                'database': db_status
            }
        })
    except Exception as e:
        logger.error(f"Error in api_status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500

@app.route('/api/config', methods=['GET'])
@require_api_enabled
def api_config():
    """Get public configuration."""
    return jsonify(get_public_config())

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({'status': 'healthy'}), 200

# Initialize database on startup
with app.app_context():
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Main entry point
def main():
    """Run the Flask application."""
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 5000)
    debug = config.get('debug', False)
    
    logger.info(f"Starting {config['app_name']} v{config['version']}")
    logger.info(f"Server will run on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()