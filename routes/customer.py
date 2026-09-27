import uuid
import random
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models import db, Category, MenuItem, CafeTable, Order, OrderItem, OrderStatusLog

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    table_num = request.args.get('table')
    if table_num:
        return redirect(url_for('customer.menu', table=table_num))
    return redirect(url_for('customer.menu'))

@customer_bp.route('/menu')
def menu():
    table_num = request.args.get('table')
    selected_table = None
    
    if table_num:
        try:
            table_int = int(table_num)
            selected_table = CafeTable.query.filter_by(table_number=table_int, is_active=True).first()
        except ValueError:
            selected_table = None
            
    active_tables = CafeTable.query.filter_by(is_active=True).order_by(CafeTable.table_number.asc()).all()
    categories = Category.query.order_by(Category.sort_order.asc()).all()
    
    # Filter menu items that are available
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    
    return render_template(
        'customer/menu.html',
        categories=categories,
        menu_items=menu_items,
        selected_table=selected_table,
        active_tables=active_tables,
        tax_rate=current_app.config['TAX_RATE']
    )

@customer_bp.route('/cart')
def cart():
    table_num = request.args.get('table')
    selected_table = None
    if table_num:
        try:
            selected_table = CafeTable.query.filter_by(table_number=int(table_num), is_active=True).first()
        except ValueError:
            pass
            
    active_tables = CafeTable.query.filter_by(is_active=True).order_by(CafeTable.table_number.asc()).all()
    return render_template(
        'customer/cart.html',
        selected_table=selected_table,
        active_tables=active_tables,
        tax_rate=current_app.config['TAX_RATE']
    )

@customer_bp.route('/order/place', methods=['POST'])
def place_order():
    data = request.get_json() if request.is_json else request.form
    
    table_number = data.get('table_number')
    customer_name = data.get('customer_name', '').strip() or 'Guest'
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])
    
    if not table_number:
        return jsonify({'success': False, 'error': 'Table number is required.'}), 400
        
    try:
        table_int = int(table_number)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid table number.'}), 400
        
    table = CafeTable.query.filter_by(table_number=table_int, is_active=True).first()
    if not table:
        return jsonify({'success': False, 'error': f'Table {table_int} is not available.'}), 404
        
    if not items_data or len(items_data) == 0:
        return jsonify({'success': False, 'error': 'Your cart is empty.'}), 400
        
    # Generate unique order number (e.g. ORD-84729)
    random_digits = random.randint(10000, 99999)
    order_number = f"ORD-{random_digits}"
    while Order.query.filter_by(order_number=order_number).first():
        order_number = f"ORD-{random.randint(10000, 99999)}"
        
    session_token = str(uuid.uuid4())
    
    # Calculate subtotal and build items
    subtotal = 0.0
    order_items = []
    
    for item in items_data:
        menu_item_id = item.get('id')
        qty = int(item.get('quantity', 1))
        if qty <= 0:
            continue
            
        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item or not menu_item.is_available:
            continue
            
        line_total = menu_item.price * qty
        subtotal += line_total
        
        order_item = OrderItem(
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            quantity=qty,
            unit_price=menu_item.price,
            line_total=line_total
        )
        order_items.append(order_item)
        
    if not order_items:
        return jsonify({'success': False, 'error': 'No valid menu items in cart.'}), 400
        
    tax_rate = current_app.config['TAX_RATE']
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    new_order = Order(
        order_number=order_number,
        table_id=table.id,
        customer_name=customer_name,
        session_token=session_token,
        status='new',
        payment_status='pending',
        payment_method='counter',
        subtotal=subtotal,
        tax=tax,
        total=total,
        notes=notes
    )
    
    db.session.add(new_order)
    db.session.flush()  # populate order.id
    
    for item in order_items:
        item.order_id = new_order.id
        db.session.add(item)
        
    # Initial status log
    status_log = OrderStatusLog(
        order_id=new_order.id,
        old_status=None,
        new_status='new',
        note='Order placed by customer from QR menu'
    )
    db.session.add(status_log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_number': order_number,
        'session_token': session_token,
        'redirect_url': url_for('customer.track_order', order_number=order_number)
    })

@customer_bp.route('/order/track/<order_number>')
def track_order(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Define step index for progress bar
    status_steps = ['new', 'accepted', 'preparing', 'ready', 'served', 'completed']
    current_step_index = 0
    if order.status in status_steps:
        current_step_index = status_steps.index(order.status)
    elif order.status == 'cancelled':
        current_step_index = -1
        
    return render_template(
        'customer/order_track.html',
        order=order,
        status_steps=status_steps,
        current_step_index=current_step_index
    )

@customer_bp.route('/api/order/<order_number>/status')
def order_status_api(order_number):
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'found': False}), 404
        
    status_steps = ['new', 'accepted', 'preparing', 'ready', 'served', 'completed']
    current_step_index = 0
    if order.status in status_steps:
        current_step_index = status_steps.index(order.status)
    elif order.status == 'cancelled':
        current_step_index = -1
        
    return jsonify({
        'found': True,
        'order_number': order.order_number,
        'status': order.status,
        'status_step_index': current_step_index,
        'payment_status': order.payment_status,
        'updated_at': order.updated_at.strftime('%I:%M:%S %p'),
        'logs': [log.to_dict() for log in order.logs]
    })
