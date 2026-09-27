import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models import db, MenuItem, Category, CafeTable, User, Order, OrderItem, OrderStatusLog
from routes.auth import admin_required, manager_required
from utils import generate_table_qr

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= MENU MANAGEMENT =================

@admin_bp.route('/menu', methods=['GET'])
@login_required
@manager_required
def menu_manage():
    categories = Category.query.order_by(Category.sort_order.asc()).all()
    menu_items = MenuItem.query.order_by(MenuItem.category_id.asc(), MenuItem.name.asc()).all()
    return render_template('admin/menu_manage.html', categories=categories, menu_items=menu_items)

@admin_bp.route('/menu/item/add', methods=['POST'])
@login_required
@manager_required
def add_menu_item():
    category_id = request.form.get('category_id')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price', '0')
    
    if not name or not category_id:
        flash("Name and category are required.", "danger")
        return redirect(url_for('admin.menu_manage'))
        
    try:
        price_val = float(price)
    except ValueError:
        price_val = 0.0
        
    image_rel_path = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            image_rel_path = f"/static/images/menu/{filename}"
            
    item = MenuItem(
        category_id=int(category_id),
        name=name,
        description=description,
        price=price_val,
        image_path=image_rel_path,
        is_available=True
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Item '{name}' added successfully.", "success")
    return redirect(url_for('admin.menu_manage'))

@admin_bp.route('/menu/item/<int:item_id>/edit', methods=['POST'])
@login_required
@manager_required
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.name = request.form.get('name', item.name).strip()
    item.category_id = int(request.form.get('category_id', item.category_id))
    item.description = request.form.get('description', item.description).strip()
    try:
        item.price = float(request.form.get('price', item.price))
    except ValueError:
        pass
        
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            item.image_path = f"/static/images/menu/{filename}"
            
    db.session.commit()
    flash(f"Item '{item.name}' updated.", "success")
    return redirect(url_for('admin.menu_manage'))

@admin_bp.route('/menu/item/<int:item_id>/toggle', methods=['POST'])
@login_required
@manager_required
def toggle_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    status_str = "Available" if item.is_available else "Unavailable"
    flash(f"'{item.name}' is now {status_str}.", "info")
    return redirect(url_for('admin.menu_manage'))

@admin_bp.route('/menu/item/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Menu item '{name}' deleted.", "warning")
    return redirect(url_for('admin.menu_manage'))

@admin_bp.route('/menu/category/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', '☕').strip()
    sort_order = int(request.form.get('sort_order', 0))
    if name:
        cat = Category(name=name, icon=icon, sort_order=sort_order)
        db.session.add(cat)
        db.session.commit()
        flash(f"Category '{name}' created.", "success")
    return redirect(url_for('admin.menu_manage'))

# ================= TABLE & QR MANAGEMENT =================

@admin_bp.route('/tables')
@login_required
@manager_required
def table_manage():
    tables = CafeTable.query.order_by(CafeTable.table_number.asc()).all()
    # Ensure every table has a valid QR
    base_url = request.host_url.rstrip('/')
    for t in tables:
        if not t.qr_code_path or not os.path.exists(os.path.join(current_app.config['BASE_DIR'], t.qr_code_path.lstrip('/'))):
            t.qr_code_path = generate_table_qr(t.table_number, base_url)
    db.session.commit()
    
    return render_template('admin/table_manage.html', tables=tables, base_url=base_url)

@admin_bp.route('/tables/add', methods=['POST'])
@login_required
@admin_required
def add_table():
    table_num = request.form.get('table_number')
    if not table_num:
        flash("Table number is required.", "danger")
        return redirect(url_for('admin.table_manage'))
        
    try:
        table_int = int(table_num)
    except ValueError:
        flash("Invalid table number.", "danger")
        return redirect(url_for('admin.table_manage'))
        
    existing = CafeTable.query.filter_by(table_number=table_int).first()
    if existing:
        flash(f"Table {table_int} already exists.", "warning")
        return redirect(url_for('admin.table_manage'))
        
    base_url = request.host_url.rstrip('/')
    qr_path = generate_table_qr(table_int, base_url)
    
    new_table = CafeTable(table_number=table_int, qr_code_path=qr_path, is_active=True)
    db.session.add(new_table)
    db.session.commit()
    flash(f"Table {table_int} added and QR code generated.", "success")
    return redirect(url_for('admin.table_manage'))

@admin_bp.route('/tables/<int:table_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_table(table_id):
    table = CafeTable.query.get_or_404(table_id)
    table.is_active = not table.is_active
    db.session.commit()
    status_str = "Active" if table.is_active else "Inactive"
    flash(f"Table {table.table_number} is now {status_str}.", "info")
    return redirect(url_for('admin.table_manage'))

@admin_bp.route('/tables/<int:table_id>/regenerate-qr', methods=['POST'])
@login_required
@admin_required
def regenerate_table_qr(table_id):
    table = CafeTable.query.get_or_404(table_id)
    base_url = request.host_url.rstrip('/')
    table.qr_code_path = generate_table_qr(table.table_number, base_url)
    db.session.commit()
    flash(f"QR code regenerated for Table {table.table_number}.", "success")
    return redirect(url_for('admin.table_manage'))

@admin_bp.route('/tables/<int:table_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_table(table_id):
    table = CafeTable.query.get_or_404(table_id)
    num = table.table_number
    db.session.delete(table)
    db.session.commit()
    flash(f"Table {num} deleted.", "warning")
    return redirect(url_for('admin.table_manage'))

# ================= STAFF MANAGEMENT =================

@admin_bp.route('/staff')
@login_required
@admin_required
def staff_manage():
    staff_members = User.query.order_by(User.role.asc(), User.name.asc()).all()
    return render_template('admin/staff_manage.html', staff_members=staff_members)

@admin_bp.route('/staff/add', methods=['POST'])
@login_required
@admin_required
def add_staff():
    work_card_id = request.form.get('work_card_id', '').strip().upper()
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'staff')
    
    if not work_card_id or not name or not password:
        flash("Work Card ID, Name, and Password are all required.", "danger")
        return redirect(url_for('admin.staff_manage'))
        
    existing = User.query.filter_by(work_card_id=work_card_id).first()
    if existing:
        flash(f"Work Card ID '{work_card_id}' is already registered to {existing.name}.", "danger")
        return redirect(url_for('admin.staff_manage'))
        
    new_user = User(
        work_card_id=work_card_id,
        name=name,
        role=role,
        is_active=True
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f"Staff member {name} ({work_card_id}) registered successfully as {role.capitalize()}.", "success")
    return redirect(url_for('admin.staff_manage'))

@admin_bp.route('/staff/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_staff(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for('admin.staff_manage'))
        
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "Active" if user.is_active else "Deactivated"
    flash(f"Staff member {user.name} is now {status_str}.", "info")
    return redirect(url_for('admin.staff_manage'))

@admin_bp.route('/staff/<int:user_id>/edit-role', methods=['POST'])
@login_required
@admin_required
def edit_staff_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'manager', 'staff']:
        user.role = new_role
        db.session.commit()
        flash(f"Role updated for {user.name} to {new_role.capitalize()}.", "success")
    return redirect(url_for('admin.staff_manage'))

# ================= ANALYTICS & REPORTS =================

@admin_bp.route('/analytics')
@login_required
@manager_required
def analytics():
    # 1. Overall Stats
    all_orders = Order.query.all()
    completed_orders = [o for o in all_orders if o.status == 'completed']
    total_revenue = sum(o.total for o in completed_orders)
    avg_order_value = (total_revenue / len(completed_orders)) if completed_orders else 0.0
    
    # 2. Daily Sales (Last 7 Days)
    today = date.today()
    last_7_days = []
    daily_revenue_data = []
    daily_order_count_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        day_orders = Order.query.filter(Order.created_at >= day_start, Order.created_at <= day_end).all()
        day_completed = [o for o in day_orders if o.status == 'completed']
        day_rev = sum(o.total for o in day_completed)
        
        last_7_days.append(day.strftime('%d %b'))
        daily_revenue_data.append(round(day_rev, 2))
        daily_order_count_data.append(len(day_orders))
        
    # 3. Staff Performance Metrics
    staff_performance = []
    staff_users = User.query.all()
    for s in staff_users:
        handled_orders = Order.query.filter_by(staff_id=s.id).all()
        completed = [o for o in handled_orders if o.status == 'completed']
        actions_count = OrderStatusLog.query.filter_by(staff_id=s.id).count()
        staff_performance.append({
            'name': s.name,
            'work_card_id': s.work_card_id,
            'role': s.role,
            'total_handled': len(handled_orders),
            'completed_count': len(completed),
            'actions_logged': actions_count
        })
    staff_performance.sort(key=lambda x: x['total_handled'], reverse=True)
    
    # 4. Peak Hours Analysis (Hour 0 to 23)
    hourly_orders = [0] * 24
    for o in all_orders:
        hour = o.created_at.hour
        hourly_orders[hour] += 1
        
    # 5. Category-wise sales breakdown
    category_sales = []
    categories = Category.query.all()
    for cat in categories:
        cat_items = MenuItem.query.filter_by(category_id=cat.id).all()
        item_ids = [it.id for it in cat_items]
        
        # Sum quantities and revenues from completed orders
        order_items = OrderItem.query.filter(OrderItem.menu_item_id.in_(item_ids)).all() if item_ids else []
        qty_sold = sum(oi.quantity for oi in order_items)
        revenue = sum(oi.line_total for oi in order_items)
        
        category_sales.append({
            'category_name': cat.name,
            'icon': cat.icon,
            'quantity_sold': qty_sold,
            'revenue': round(revenue, 2)
        })
    category_sales.sort(key=lambda x: x['revenue'], reverse=True)
    
    return render_template(
        'admin/analytics.html',
        total_orders=len(all_orders),
        completed_orders_count=len(completed_orders),
        total_revenue=round(total_revenue, 2),
        avg_order_value=round(avg_order_value, 2),
        days_labels=last_7_days,
        daily_revenue=daily_revenue_data,
        daily_orders=daily_order_count_data,
        staff_performance=staff_performance,
        hourly_orders=hourly_orders,
        category_sales=category_sales
    )

# ================= ORDER HISTORY =================

@admin_bp.route('/history')
@login_required
@manager_required
def order_history():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Order.query
    if search:
        query = query.filter(
            (Order.order_number.ilike(f'%{search}%')) |
            (Order.customer_name.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter_by(status=status)
    if start_date:
        try:
            s_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= s_dt)
        except ValueError:
            pass
    if end_date:
        try:
            e_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < e_dt)
        except ValueError:
            pass
            
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template(
        'admin/order_history.html',
        orders=orders,
        search=search,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
