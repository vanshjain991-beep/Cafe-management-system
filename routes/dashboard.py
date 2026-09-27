from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Order, OrderItem, OrderStatusLog, CafeTable, User

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def home():
    # Active orders (not completed, not cancelled)
    active_orders = Order.query.filter(
        Order.status.notin_(['completed', 'cancelled'])
    ).order_by(Order.created_at.asc()).all()
    
    # Categorize into status buckets for Kanban display
    new_orders = [o for o in active_orders if o.status == 'new']
    accepted_orders = [o for o in active_orders if o.status == 'accepted']
    preparing_orders = [o for o in active_orders if o.status == 'preparing']
    ready_orders = [o for o in active_orders if o.status == 'ready']
    served_orders = [o for o in active_orders if o.status == 'served']
    
    # Today's stats
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_orders = Order.query.filter(Order.created_at >= today_start).all()
    today_completed = [o for o in today_orders if o.status == 'completed']
    today_revenue = sum(o.total for o in today_completed)
    
    return render_template(
        'dashboard/home.html',
        active_orders=active_orders,
        new_orders=new_orders,
        accepted_orders=accepted_orders,
        preparing_orders=preparing_orders,
        ready_orders=ready_orders,
        served_orders=served_orders,
        today_total_orders=len(today_orders),
        today_revenue=today_revenue,
        today_completed_count=len(today_completed)
    )

@dashboard_bp.route('/orders')
@login_required
def orders_list():
    status_filter = request.args.get('status', '')
    table_filter = request.args.get('table', '')
    
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if table_filter:
        try:
            table_int = int(table_filter)
            query = query.join(CafeTable).filter(CafeTable.table_number == table_int)
        except ValueError:
            pass
            
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    tables = CafeTable.query.order_by(CafeTable.table_number.asc()).all()
    
    return render_template(
        'dashboard/orders.html',
        orders=orders,
        tables=tables,
        selected_status=status_filter,
        selected_table=table_filter
    )

@dashboard_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('dashboard/order_detail.html', order=order)

@dashboard_bp.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    note = request.form.get('note', '').strip()
    
    valid_statuses = ['new', 'accepted', 'preparing', 'ready', 'served', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        flash("Invalid status transition.", "danger")
        return redirect(request.referrer or url_for('dashboard.home'))
        
    old_status = order.status
    order.status = new_status
    
    # Assign or update staff handler
    if not order.staff_id or current_user.is_staff:
        order.staff_id = current_user.id
        
    # If completed and paid at counter, automatically mark paid if requested
    if new_status == 'completed' and request.form.get('mark_paid') == 'yes':
        order.payment_status = 'paid'
        
    log = OrderStatusLog(
        order_id=order.id,
        staff_id=current_user.id,
        old_status=old_status,
        new_status=new_status,
        note=note or f"Updated to {new_status} by {current_user.name} ({current_user.work_card_id})"
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"Order #{order.order_number} status updated to {new_status.capitalize()}.", "success")
    
    # Support AJAX response if requested
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'new_status': new_status})
        
    return redirect(request.referrer or url_for('dashboard.home'))

@dashboard_bp.route('/order/<int:order_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_status = 'paid'
    
    log = OrderStatusLog(
        order_id=order.id,
        staff_id=current_user.id,
        old_status=order.status,
        new_status=order.status,
        note=f"Payment marked as PAID at counter by {current_user.name}"
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"Payment marked as PAID for Order #{order.order_number}.", "success")
    return redirect(request.referrer or url_for('dashboard.order_detail', order_id=order.id))
