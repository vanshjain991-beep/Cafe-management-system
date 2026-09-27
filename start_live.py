import subprocess
import time
import re
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from app import create_app
from models import db, CafeTable
from utils import generate_table_qr

def update_qrs_with_url(public_url):
    app = create_app()
    with app.app_context():
        tables = CafeTable.query.all()
        for t in tables:
            t.qr_code_path = generate_table_qr(t.table_number, public_url)
            print(f"Updated QR for Table {t.table_number} -> {public_url}/menu?table={t.table_number}")
        db.session.commit()
    print(f"All QR codes successfully mapped to {public_url}!")

def main():
    print("Starting Flask application...")
    flask_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(2)
    print("Starting Cloudflare Public Tunnel...")
    cf_proc = subprocess.Popen(
        ["cloudflared.exe", "tunnel", "--url", "http://127.0.0.1:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    public_url = None
    # Read output until trycloudflare.com URL is found
    for line in cf_proc.stdout:
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        print("\n" + "="*60)
        print("YOUR WEBSITE IS LIVE WORLDWIDE ON THE INTERNET!")
        print(f"Live Public URL: {public_url}")
        print(f"Customer Menu:   {public_url}/menu?table=1")
        print(f"Staff Portal:    {public_url}/login")
        print("="*60 + "\n")

        # Write the public URL to a file
        with open("live_url.txt", "w", encoding="utf-8") as f:
            f.write(public_url)

        # Update QR codes so scanning them opens this public URL!
        try:
            update_qrs_with_url(public_url)
        except Exception as e:
            print(f"Note on QR update: {e}")

        # Keep running
        try:
            cf_proc.wait()
        except KeyboardInterrupt:
            pass
    else:
        print("Failed to detect Cloudflare Tunnel URL.")

    flask_proc.terminate()
    cf_proc.terminate()

if __name__ == '__main__':
    main()
