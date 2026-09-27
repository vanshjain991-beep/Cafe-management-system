from datetime import datetime, date
from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import Order, CafeTable, MenuItem

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/orders/live')
@login_required
def live_orders():
    """
    Returns list of active orders for staff dashboard live updates.
    """
    active_orders = Order.query.filter(
        Order.status.notin_(['completed', 'cancelled'])
    ).order_by(Order.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'total_active': len(active_orders),
        'orders': [o.to_dict() for o in active_orders]
    })

@api_bp.route('/stats/live')
@login_required
def live_stats():
    """
    Returns summary counters for staff header/badges.
    """
    active_orders = Order.query.filter(
        Order.status.notin_(['completed', 'cancelled'])
    ).all()
    
    new_count = sum(1 for o in active_orders if o.status == 'new')
    accepted_count = sum(1 for o in active_orders if o.status == 'accepted')
    preparing_count = sum(1 for o in active_orders if o.status == 'preparing')
    ready_count = sum(1 for o in active_orders if o.status == 'ready')
    served_count = sum(1 for o in active_orders if o.status == 'served')
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_completed = Order.query.filter(Order.created_at >= today_start, Order.status == 'completed').all()
    today_revenue = sum(o.total for o in today_completed)
    
    return jsonify({
        'success': True,
        'new_count': new_count,
        'accepted_count': accepted_count,
        'preparing_count': preparing_count,
        'ready_count': ready_count,
        'served_count': served_count,
        'today_completed_count': len(today_completed),
        'today_revenue': round(today_revenue, 2)
    })
