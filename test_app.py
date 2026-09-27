import sys
import unittest
from app import create_app
from models import db, User, CafeTable, MenuItem, Order, OrderStatusLog

class CoffeeAndLoveTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_public_routes(self):
        # Home redirects to menu
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)

        # Menu page with and without table
        res = self.client.get('/menu')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'COFFEE', res.data)

        res = self.client.get('/menu?table=2')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Table 2', res.data)

        # Cart page
        res = self.client.get('/cart?table=2')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Your Order Cart', res.data)

    def test_02_staff_login_and_roles(self):
        # Login page renders
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Work Card ID', res.data)

        # Login with Admin card
        res = self.client.post('/login', data={
            'work_card_id': 'ADMIN001',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Live Orders Command Center', res.data)

        # Access Admin protected pages
        res = self.client.get('/admin/menu')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/admin/tables')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Table 1', res.data)

        res = self.client.get('/admin/staff')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'ADMIN001', res.data)

        res = self.client.get('/admin/analytics')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Daily Revenue Trend', res.data)

        res = self.client.get('/admin/history')
        self.assertEqual(res.status_code, 200)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_03_order_placement_and_tracking(self):
        with self.app.app_context():
            item = MenuItem.query.first()
            self.assertIsNotNone(item)
            item_id = item.id
            item_price = item.price

        # Customer places order via API
        order_payload = {
            'table_number': 3,
            'customer_name': 'Test Guest',
            'notes': 'Extra foam',
            'items': [
                {'id': item_id, 'quantity': 2, 'price': item_price}
            ]
        }

        res = self.client.post('/order/place', json=order_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        order_number = data['order_number']

        # Live tracking page
        res = self.client.get(f'/order/track/{order_number}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(order_number.encode(), res.data)

        # Live polling API
        res = self.client.get(f'/api/order/{order_number}/status')
        self.assertEqual(res.status_code, 200)
        status_data = res.get_json()
        self.assertEqual(status_data['status'], 'new')

    def test_04_status_progression_and_settlement(self):
        # Login as staff
        self.client.post('/login', data={'work_card_id': 'STF101', 'password': 'staff123'})

        with self.app.app_context():
            order = Order.query.filter_by(status='new').first()
            self.assertIsNotNone(order)
            order_id = order.id

        # Accept order
        res = self.client.post(f'/dashboard/order/{order_id}/update-status', data={
            'status': 'accepted',
            'note': 'Order acknowledged by Vineet'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check status changed
        with self.app.app_context():
            updated = Order.query.get(order_id)
            self.assertEqual(updated.status, 'accepted')
            self.assertIsNotNone(updated.staff_id)

        # Advance to completed and paid
        res = self.client.post(f'/dashboard/order/{order_id}/update-status', data={
            'status': 'completed',
            'mark_paid': 'yes',
            'note': 'Bill settled at counter'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            updated = Order.query.get(order_id)
            self.assertEqual(updated.status, 'completed')
            self.assertEqual(updated.payment_status, 'paid')

if __name__ == '__main__':
    unittest.main()
