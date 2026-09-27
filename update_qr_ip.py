from app import create_app
from models import db, CafeTable
from utils import generate_table_qr

app = create_app()

def update_qrs(ip="10.207.88.213", port=5000):
    with app.app_context():
        base_url = f"http://{ip}:{port}"
        tables = CafeTable.query.all()
        for t in tables:
            t.qr_code_path = generate_table_qr(t.table_number, base_url)
            print(f"Generated QR for Table {t.table_number} -> {base_url}/menu?table={t.table_number}")
        db.session.commit()
        print("All QR codes updated with LAN IP!")

if __name__ == '__main__':
    update_qrs()
