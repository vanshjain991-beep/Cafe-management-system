from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required for this action.", "danger")
            return redirect(url_for('dashboard.home'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager:
            flash("Manager or Admin access required.", "danger")
            return redirect(url_for('dashboard.home'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
        
    if request.method == 'POST':
        work_card_id = request.form.get('work_card_id', '').strip().upper()
        password = request.form.get('password', '')
        
        if not work_card_id or not password:
            flash("Please enter both Work Card ID and Password.", "warning")
            return render_template('dashboard/login.html')
            
        user = User.query.filter_by(work_card_id=work_card_id).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash("This staff account has been deactivated. Please contact Admin.", "danger")
                return render_template('dashboard/login.html')
                
            login_user(user)
            flash(f"Welcome back, {user.name} ({user.role.capitalize()})!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.home'))
        else:
            flash("Invalid Work Card ID or Password.", "danger")
            
    return render_template('dashboard/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.name
    logout_user()
    flash(f"Logged out successfully. Have a nice day, {name}!", "info")
    return redirect(url_for('auth.login'))
