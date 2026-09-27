import os
import random
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Category, MenuItem, CafeTable, Order, OrderItem, OrderStatusLog
from utils import generate_table_qr

app = create_app()

def seed_database():
    with app.app_context():
        print("Cleaning and initializing database...")
        db.drop_all()
        db.create_all()
        
        # 1. Staff Members
        print("Seeding staff accounts...")
        staff_data = [
            {'card': 'ADMIN001', 'name': 'Vansh Jain', 'role': 'admin', 'pass': 'admin123'},
            {'card': 'MGR001', 'name': 'Sumit Tiwari', 'role': 'manager', 'pass': 'mgr123'},
            {'card': 'STF101', 'name': 'Vineet Singh', 'role': 'staff', 'pass': 'staff123'},
            {'card': 'STF102', 'name': 'Priya Patel', 'role': 'staff', 'pass': 'staff123'},
        ]
        
        users = []
        for s in staff_data:
            user = User(
                work_card_id=s['card'],
                name=s['name'],
                role=s['role'],
                is_active=True
            )
            user.set_password(s['pass'])
            db.session.add(user)
            users.append(user)
        db.session.commit()
        
        # 2. Tables & QR codes
        print("Seeding 8 cafe tables and generating QR badges...")
        base_url = "http://localhost:5000"
        tables = []
        for num in range(1, 9):
            qr_path = generate_table_qr(num, base_url)
            table = CafeTable(table_number=num, qr_code_path=qr_path, is_active=True)
            db.session.add(table)
            tables.append(table)
        db.session.commit()
        
        # 3. Categories & Menu Items
        print("Seeding categories and menu items...")
        menu_catalog = [
            {
                'category': 'Hot Beverages',
                'icon': '☕',
                'items': [
                    {'name': 'Espresso Doppio', 'price': 120.0, 'desc': 'Rich double shot of dark roasted Arabica beans.'},
                    {'name': 'Cappuccino Italiano', 'price': 150.0, 'desc': 'Equal parts espresso, steamed milk, and velvety foam dusted with cocoa.'},
                    {'name': 'Classic Cafe Latte', 'price': 160.0, 'desc': 'Smooth espresso blended with creamy microfoam milk.'},
                    {'name': 'Caramel Macchiato', 'price': 180.0, 'desc': 'Freshly steamed milk with vanilla, marked with espresso and caramel drizzle.'},
                    {'name': 'Belgian Hot Chocolate', 'price': 170.0, 'desc': 'Decadent melted Belgian chocolate with hot milk and mini marshmallows.'},
                ]
            },
            {
                'category': 'Cold Beverages',
                'icon': '🧊',
                'items': [
                    {'name': 'Signature Cold Brew', 'price': 170.0, 'desc': 'Steeped for 18 hours for maximum smoothness and low acidity.'},
                    {'name': 'Iced Caramel Frappe', 'price': 190.0, 'desc': 'Blended coffee, ice, cream, topped with whipped cream and golden caramel.'},
                    {'name': 'Iced Peach & Passion Tea', 'price': 150.0, 'desc': 'Refreshing black tea infused with sweet peach and passion fruit notes.'},
                    {'name': 'Tropical Mango Smoothie', 'price': 180.0, 'desc': 'Fresh Alphonso mango pulp blended with Greek yogurt and honey.'},
                    {'name': 'Hazelnut Cold Coffee', 'price': 160.0, 'desc': 'Creamy iced coffee infused with roasted hazelnut syrup.'},
                ]
            },
            {
                'category': 'Snacks & Savories',
                'icon': '🥪',
                'items': [
                    {'name': 'Paneer Tikka Grilled Wrap', 'price': 180.0, 'desc': 'Tandoori spiced paneer cubes, crunchy peppers and mint mayonnaise.'},
                    {'name': 'Classic Club Sandwich', 'price': 190.0, 'desc': 'Triple-decker toasted sourdough with cheese, garden greens, and house dressing.'},
                    {'name': 'Crispy Peri Peri Fries', 'price': 130.0, 'desc': 'Golden French fries tossed in spicy peri-peri dust with garlic dip.'},
                    {'name': 'Cheesy Garlic Bread', 'price': 140.0, 'desc': 'Artisan baguette with melted mozzarella and fragrant herb butter.'},
                    {'name': 'Loaded Cheese Nachos', 'price': 195.0, 'desc': 'Corn tortillas smothered in hot queso, salsa fresca, jalapenos, and sour cream.'},
                ]
            },
            {
                'category': 'Desserts',
                'icon': '🍰',
                'items': [
                    {'name': 'Sizzling Chocolate Brownie', 'price': 160.0, 'desc': 'Fudgy walnut brownie served warm with vanilla gelato and hot fudge.'},
                    {'name': 'New York Baked Cheesecake', 'price': 210.0, 'desc': 'Dense, creamy cheesecake with a buttery graham crust and berry coulis.'},
                    {'name': 'Classic Coffee Tiramisu', 'price': 220.0, 'desc': 'Savoiardi dipped in espresso, layered with whipped mascarpone cream.'},
                    {'name': 'Blueberry Crumble Muffin', 'price': 110.0, 'desc': 'Soft bakery muffin bursting with wild blueberries and oat crumble.'},
                ]
            }
        ]
        
        all_menu_items = []
        for idx, cat_data in enumerate(menu_catalog):
            cat = Category(name=cat_data['category'], icon=cat_data['icon'], sort_order=idx + 1)
            db.session.add(cat)
            db.session.flush()
            
            for it in cat_data['items']:
                menu_item = MenuItem(
                    category_id=cat.id,
                    name=it['name'],
                    description=it['desc'],
                    price=it['price'],
                    image_path='',  # Using stylized CSS icons/badges when images are not uploaded
                    is_available=True
                )
                db.session.add(menu_item)
                all_menu_items.append(menu_item)
        db.session.commit()
        
        # 4. Seed Demo Orders for presentation
        print("Seeding sample orders across different stages of the lifecycle...")
        admin_user = users[0]
        mgr_user = users[1]
        staff1 = users[2]
        staff2 = users[3]
        
        # Helper to create order
        def create_sample_order(order_no, table, staff, customer, status, items_spec, mins_ago, payment='pending'):
            created_time = datetime.utcnow() - timedelta(minutes=mins_ago)
            subtotal = sum(item[0].price * item[1] for item in items_spec)
            tax = subtotal * 0.05
            total = subtotal + tax
            
            order = Order(
                order_number=order_no,
                table_id=table.id,
                staff_id=staff.id if staff else None,
                customer_name=customer,
                session_token=f"demo-token-{order_no}",
                status=status,
                payment_status=payment,
                payment_method='counter',
                subtotal=subtotal,
                tax=tax,
                total=total,
                notes='Extra napkins please.' if random.choice([True, False]) else '',
                created_at=created_time,
                updated_at=created_time + timedelta(minutes=2)
            )
            db.session.add(order)
            db.session.flush()
            
            for item, qty in items_spec:
                oi = OrderItem(
                    order_id=order.id,
                    menu_item_id=item.id,
                    item_name=item.name,
                    quantity=qty,
                    unit_price=item.price,
                    line_total=item.price * qty
                )
                db.session.add(oi)
                
            # Log lifecycle
            statuses = ['new']
            if status in ['accepted', 'preparing', 'ready', 'served', 'completed']:
                statuses.append('accepted')
            if status in ['preparing', 'ready', 'served', 'completed']:
                statuses.append('preparing')
            if status in ['ready', 'served', 'completed']:
                statuses.append('ready')
            if status in ['served', 'completed']:
                statuses.append('served')
            if status == 'completed':
                statuses.append('completed')
                
            for i, st in enumerate(statuses):
                log = OrderStatusLog(
                    order_id=order.id,
                    staff_id=staff.id if staff else None,
                    old_status=statuses[i-1] if i > 0 else None,
                    new_status=st,
                    note=f"Status set to {st}",
                    changed_at=created_time + timedelta(minutes=i*3)
                )
                db.session.add(log)
                
            return order

        # Sample Orders:
        # Order 1: New order on Table 1
        create_sample_order(
            "ORD-40101", tables[0], None, "Aarav Sharma", "new",
            [(all_menu_items[1], 2), (all_menu_items[11], 1)],  # 2 Cappuccinos, 1 Peri Peri Fries
            mins_ago=5
        )
        
        # Order 2: Accepted order on Table 3
        create_sample_order(
            "ORD-40102", tables[2], staff1, "Rohan Verma", "accepted",
            [(all_menu_items[2], 1), (all_menu_items[10], 1)],  # 1 Latte, 1 Club Sandwich
            mins_ago=12
        )
        
        # Order 3: Preparing order on Table 2
        create_sample_order(
            "ORD-40103", tables[1], staff2, "Neha Gupta", "preparing",
            [(all_menu_items[6], 2), (all_menu_items[14], 1)],  # 2 Caramel Frappes, 1 Sizzling Brownie
            mins_ago=25
        )
        
        # Order 4: Ready order on Table 5
        create_sample_order(
            "ORD-40104", tables[4], staff1, "Karan Singh", "ready",
            [(all_menu_items[5], 1), (all_menu_items[12], 1)],  # 1 Cold Brew, 1 Cheesy Garlic Bread
            mins_ago=35
        )
        
        # Order 5: Served order on Table 4
        create_sample_order(
            "ORD-40105", tables[3], staff2, "Meera Roy", "served",
            [(all_menu_items[3], 2), (all_menu_items[15], 1)],  # 2 Caramel Macchiatos, 1 NY Cheesecake
            mins_ago=45
        )
        
        # Order 6: Completed and Paid order on Table 6
        create_sample_order(
            "ORD-40106", tables[5], mgr_user, "Vikram Malhotra", "completed",
            [(all_menu_items[0], 2), (all_menu_items[16], 2)],  # 2 Espressos, 2 Tiramisus
            mins_ago=75, payment='paid'
        )

        # Order 7: Completed and Paid order on Table 7
        create_sample_order(
            "ORD-40107", tables[6], admin_user, "Ananya Sen", "completed",
            [(all_menu_items[7], 1), (all_menu_items[9], 1)],  # 1 Peach Tea, 1 Paneer Wrap
            mins_ago=120, payment='paid'
        )
        
        db.session.commit()
        print("\n[SUCCESS] Database seeded successfully!")
        print("--------------------------------------------------")
        print("Admin login:   ADMIN001 / admin123")
        print("Manager login: MGR001   / mgr123")
        print("Staff login:   STF101   / staff123")
        print("Staff login:   STF102   / staff123")
        print("--------------------------------------------------")

if __name__ == '__main__':
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    seed_database()
