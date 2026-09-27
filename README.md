# ☕ COFFEE & LOVE — Smart Cafe Management System

> **B.Tech CSE (B) 2nd Year Mini Project Presentation** (Session 2026-27)  
> **Presented by:** Sumit Tiwari (117), Vansh Jain (128), Vineet Singh (133)  
> **Guide:** Prof. Amit Rawat  

---

## 🌟 Overview

**COFFEE & LOVE** is a full-stack, QR-code powered web application built for modern cafes and lounges. It streamlines cafe operations by eliminating paper menus, manual billing calculations, and order miscommunication. 

Customers scan a table-specific QR code on their phone to access the live digital menu, customize orders, and track progress from the kitchen to their table in real-time. Meanwhile, cafe staff and managers use a role-based operations dashboard with live Kanban order tracking, audit trails, and business analytics.

---

## 🚀 Key Features

1. **📱 Table-Specific QR Code Ordering**
   - Each dining table has a unique, branded QR code.
   - Scanning automatically identifies the table number on the customer's phone without requiring account sign-up.

2. **☕ Live Digital Menu with Instant Search & Filtering**
   - Handcrafted categories: Hot Beverages, Cold Beverages, Snacks & Savories, Desserts.
   - Real-time client-side search across item names and descriptions.

3. **🛒 Cart & Order Management**
   - Interactive item quantity increment/decrement controls.
   - Special cooking instructions & preferences input (e.g., "Less sugar", "Extra hot").
   - Persistent cart state using browser `localStorage`.

4. **🧾 Automated Billing & GST Calculations**
   - Subtotal, CGST (2.5%), SGST (2.5%), and Grand Total automatically computed.
   - Built-in "Pay at Counter" flow with printable receipt/invoice format (`window.print()`).

5. **📊 6-Stage Order Lifecycle & Real-Time Tracking**
   - Customer tracking with visual animated stepper: `Placed` → `Accepted` → `In Kitchen` → `Ready` → `Served` → `Completed`.
   - Auto-polling updates status live on the customer's screen without page refresh.

6. **📋 Staff Operations Command Center (Kanban View)**
   - 5-column live board (`New`, `Accepted`, `Preparing`, `Ready`, `Served`).
   - Web Audio chime alert when a new order arrives.
   - One-click status advancement and staff assignment.

7. **👥 Role-Based Staff Authentication (Work Card ID)**
   - Login using physical Work Card ID (e.g. `ADMIN001`, `MGR001`, `STF101`) + password.
   - 3 access levels:
     - **Admin**: Full control over menu, tables, staff accounts, analytics.
     - **Manager**: Menu editing, table oversight, business reports.
     - **Staff**: Order reception, preparation, and table service.

8. **📈 Cafe Business Intelligence & Analytics**
   - Daily gross revenue and order volume trends.
   - Staff performance and productivity metrics (orders fulfilled & actions logged).
   - Peak hours distribution (08:00 to 22:00 analysis).
   - Category-wise sales contribution and popular items.
   - Complete historical order archive with date and text filters.

---

## 🛠️ Technology Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite via Flask-SQLAlchemy
- **Authentication:** Flask-Login + Werkzeug Secure Password Hashing
- **Frontend:** Vanilla HTML5, CSS3 (Custom Dark/Moody Theme with Gold & Amber accents), Modern JavaScript (ES6+)
- **QR Code Generation:** Python `qrcode` + `Pillow` (PIL)
- **Templating:** Jinja2

---

## 🏃 How to Run the Project

### 1. Open Terminal in Project Directory
```powershell
cd C:\Users\vansh\.gemini\antigravity\scratch\coffee-and-love
```

### 2. Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Run the Server
```powershell
python app.py
```
The server will start on: **`http://localhost:5000`** (and on `http://<your-local-ip>:5000` for mobile devices on the same WiFi network).

---

## 🔑 Demo Presentation Credentials

| Role | Work Card ID | Password | Access Level |
|------|-------------|----------|--------------|
| **Admin** | `ADMIN001` | `admin123` | Full system access, staff, tables, analytics |
| **Manager** | `MGR001` | `mgr123` | Menu, tables, reports, orders |
| **Staff (Barista)** | `STF101` | `staff123` | Kitchen prep & order status |
| **Staff (Server)** | `STF102` | `staff123` | Table service & bill settlement |

---

## 🎬 How to Demo During Presentation

1. **Customer Order Demo:**
   - Go to `http://localhost:5000/menu?table=3` (or scan Table 3 QR code from `static/qrcodes/table_3.png`).
   - Add a *Cappuccino Italiano* and *Warm Brownie* to cart.
   - Click **View Cart** → click **Confirm & Place Order**.
   - Note the live tracking screen with the 6-stage visual progress bar!

2. **Staff Kitchen Board Demo:**
   - In another tab or split window, go to `http://localhost:5000/login`.
   - Log in with `STF101` / `staff123`.
   - Observe the live Kanban board — the new order appears under **New Orders** with a chime!
   - Click **✓ Accept** → **☕ Prepare** → **🛎️ Ready** → **🍽️ Serve**.
   - Watch the customer's tab automatically advance live without manual reload!

3. **Settling & Receipt Demo:**
   - Click **💰 Settle Bill** or view order detail to print the customer thermal receipt.

4. **Analytics Demo:**
   - Log in as `ADMIN001` / `admin123` and open **📈 Analytics** to showcase daily revenue charts, peak hours, category breakdown, and staff productivity reports.
