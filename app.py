import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.api import api_bp

login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
    
    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please sign in with your Work Card ID to access this page."
    login_manager.login_message_category = "warning"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Global template context processor
    @app.context_processor
    def inject_global_vars():
        return {
            'cafe_name': app.config.get('CAFE_NAME', 'COFFEE & LOVE'),
            'cafe_tagline': app.config.get('CAFE_TAGLINE', 'Brewed with Passion, Served with Warmth'),
            'currency': app.config.get('CURRENCY_SYMBOL', '₹'),
            'tax_rate_percent': int(app.config.get('TAX_RATE', 0.05) * 100),
            'current_year': datetime.now().year
        }
        
    # Register blueprints
    app.register_blueprint(customer_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', content="<div class='error-page'><h2>404</h2><p>Page Not Found</p><a href='/' class='btn btn-primary'>Go to Menu</a></div>"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', content="<div class='error-page'><h2>500</h2><p>Internal Server Error</p><a href='/' class='btn btn-primary'>Go to Menu</a></div>"), 500

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Runs on all network interfaces so phones on the same WiFi can scan QR codes!
    app.run(host='0.0.0.0', port=5000, debug=True)
