from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    work_card_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin', 'manager', 'staff'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders_handled = db.relationship('Order', backref='handler', lazy=True, foreign_keys='Order.staff_id')
    status_logs = db.relationship('OrderStatusLog', backref='staff', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_admin(self):
        return self.role == 'admin'
        
    @property
    def is_manager(self):
        return self.role in ['admin', 'manager']
        
    @property
    def is_staff(self):
        return self.role == 'staff'
        
    def to_dict(self):
        return {
            'id': self.id,
            'work_card_id': self.work_card_id,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='☕')
    sort_order = db.Column(db.Integer, default=0)
    
    items = db.relationship('MenuItem', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'item_count': len(self.items)
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), default='')
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image_path': self.image_path,
            'is_available': self.is_available
        }


class CafeTable(db.Model):
    __tablename__ = 'cafe_tables'
    
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, unique=True, nullable=False)
    qr_code_path = db.Column(db.String(255), default='')
    is_active = db.Column(db.Boolean, default=True)
    
    orders = db.relationship('Order', backref='table', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'qr_code_path': self.qr_code_path,
            'is_active': self.is_active
        }


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    table_id = db.Column(db.Integer, db.ForeignKey('cafe_tables.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), default='Guest')
    session_token = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(30), default='new', index=True)
    # Order Status Lifecycle: new -> accepted -> preparing -> ready -> served -> completed | cancelled
    payment_status = db.Column(db.String(20), default='pending')  # 'pending', 'paid'
    payment_method = db.Column(db.String(50), default='counter')  # 'counter', 'upi_qr'
    subtotal = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('OrderStatusLog', backref='order', lazy=True, cascade='all, delete-orphan', order_by='OrderStatusLog.changed_at.asc()')
    
    @property
    def formatted_time(self):
        return self.created_at.strftime('%I:%M %p')
        
    @property
    def formatted_date(self):
        return self.created_at.strftime('%d %b %Y')
        
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'table_number': self.table.table_number if self.table else None,
            'table_id': self.table_id,
            'staff_name': self.handler.name if self.handler else 'Unassigned',
            'customer_name': self.customer_name,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'subtotal': round(self.subtotal, 2),
            'tax': round(self.tax, 2),
            'total': round(self.total, 2),
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=True)
    item_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'unit_price': round(self.unit_price, 2),
            'line_total': round(self.line_total, 2)
        }


class OrderStatusLog(db.Model):
    __tablename__ = 'order_status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(255), default='')
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'staff_name': self.staff.name if self.staff else 'System',
            'old_status': self.old_status,
            'new_status': self.new_status,
            'note': self.note,
            'changed_at': self.changed_at.strftime('%Y-%m-%d %H:%M:%S')
        }
