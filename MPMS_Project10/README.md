# 🔍 Missing Person Management System (MPMS) v2.0

A full-featured, production-ready web application for managing missing person cases in Pakistan, built with Python Flask + SQLite.

---

## 🚀 Quick Start (3 Steps)

```bash
# Step 1: Install Python dependencies
pip install -r requirements.txt

# Step 2: Run the app
python app.py

# Step 3: Open your browser
# Visit: http://localhost:5000
```

The database is created automatically with sample data on first run. ✅

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | `admin1` | `Admin@123` | Full system access |
| **Police** | `officer1` | `Police@123` | Case management |
| **Police** | `officer2` | `Police@456` | Case management |
| **Law Enforcement** | `law1` | `Law@123` | Case management |
| **Public** | `public1` | `Public@123` | Report & view cases |

---

## ✨ Features

### 🔐 Authentication & Security
- **PBKDF2-SHA256** password hashing (600,000 iterations)
- **Account lockout** after 5 failed login attempts (15-minute cooldown)
- **Forgot password** with secure token-based reset (SHA-256 hashed tokens)
- **Password strength** indicator (weak/fair/good/strong)
- **Change password** from profile page
- **Session-based auth** with 8-hour timeout
- **Audit logging** of all user actions with IP addresses
- **Role-based access control** (4 roles)

### 📋 Case Management
- Create, read, update, delete missing person cases
- Auto-generated case numbers (MP-YYYY-XXXX format)
- Full case timeline (every update logged with who/when)
- Search by name, case number, CNIC, location
- Filter by status and priority
- Table view and card view toggle
- CNIC / National ID storage
- Medical information tracking

### 🚨 Alert System
- Issue AMBER / SILVER / CRITICAL alerts
- Dismiss alerts when resolved
- Real-time alert display

### 🔔 Notification System
- Real-time in-app notifications
- Notification bell with unread count badge
- Mark individual or all notifications as read
- Notifications for: new cases, status changes, account events

### 👥 User Management (Admin only)
- Add, edit, delete users
- Unlock locked accounts
- Role assignment
- Badge number and contact info

### 📊 Dashboard
- Live statistics (total, missing, located, critical, alerts)
- Monthly bar chart (Chart.js)
- Status donut chart
- Recent cases list
- Active alerts panel

### 📝 Audit Log (Admin only)
- Full trail of all system actions
- User, action, details, IP, timestamp

---

## 📁 Project Structure

```
missing_persons_system/
├── app.py                      # Main Flask app (862 lines)
│                               # Models, routes, auth, API endpoints
├── requirements.txt            # Python dependencies
├── database/
│   └── mpms.db                 # SQLite database (auto-created)
├── templates/
│   ├── base.html               # Layout: sidebar, topbar, notifications
│   ├── login.html              # Login with role selector
│   ├── forgot_password.html    # Password reset request
│   ├── reset_password.html     # Set new password
│   ├── dashboard.html          # Stats + charts + recent cases
│   ├── cases.html              # Case CRUD with search/filter
│   ├── alerts.html             # Alert management
│   ├── users.html              # User management (Admin)
│   ├── profile.html            # Profile + change password
│   └── audit.html              # Audit trail (Admin)
├── static/
│   ├── css/main.css            # Full dark theme stylesheet
│   └── js/
│       ├── app.js              # Shared: clock, notifications, modals
│       ├── login.js            # Login form + attempt warnings
│       ├── dashboard.js        # Chart.js charts
│       ├── cases.js            # Case CRUD operations
│       ├── alerts.js           # Alert management
│       └── users.js            # User CRUD operations
├── screenshots/                # Interface screenshots (19 images)
├── SRS_Document.md             # Software Requirements Specification
└── README.md                   # This file
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Database | SQLite (via Flask-SQLAlchemy ORM) |
| Auth | Werkzeug (PBKDF2-SHA256), itsdangerous |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| Charts | Chart.js v4 |
| Screenshots | Playwright (for documentation) |

---

## 🚢 Deployment Options

### Option 1: Local Development (Default)
```bash
pip install -r requirements.txt
python app.py
# App runs at http://localhost:5000
```

### Option 2: Production with Gunicorn (Linux/Mac)
```bash
pip install gunicorn
gunicorn app:app -w 4 -b 0.0.0.0:8000
# App runs at http://YOUR_IP:8000
```

### Option 3: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn
COPY . .
EXPOSE 8000
CMD ["gunicorn", "app:app", "-w", "2", "-b", "0.0.0.0:8000"]
```
```bash
docker build -t mpms .
docker run -p 8000:8000 -v $(pwd)/database:/app/database mpms
```

### Option 4: PythonAnywhere (Free Cloud Hosting)
1. Sign up at pythonanywhere.com
2. Upload project files via Files tab
3. Open a Bash console: `pip install flask flask-sqlalchemy werkzeug itsdangerous`
4. Set up a Web app: Manual config → Python 3.11
5. Set WSGI file to import `app` from your project
6. Reload — your app is live at `yourusername.pythonanywhere.com`

### Option 5: Render.com (Free Tier)
```yaml
# render.yaml
services:
  - type: web
    name: mpms
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

### Option 6: Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## 🔧 Environment Variables (Production)

```bash
export SECRET_KEY="your-very-long-random-secret-key-here"
export FLASK_ENV=production
```

Or create a `.env` file:
```
SECRET_KEY=your-very-long-random-secret-key-here
```

---

## 🗄 Database

SQLite is used for simplicity. For production scale, switch to PostgreSQL:

```python
# In app.py, replace:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/mpms.db'

# With:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/mpms'
```

Then: `pip install psycopg2-binary`

---

## 📊 Database Models

| Model | Description |
|-------|-------------|
| `User` | System users (all roles), with password hash, lockout, reset token |
| `MissingPerson` | Case records with all person details |
| `CaseUpdate` | Timeline entries for every case change |
| `Alert` | AMBER/SILVER/CRITICAL alerts |
| `Notification` | Per-user in-app notifications |
| `AuditLog` | System-wide action audit trail |

---

## 🔒 Security Notes

- Passwords use PBKDF2-SHA256 with 600,000 iterations — industry standard
- Reset tokens are SHA-256 hashed before storage (token itself is never stored)
- Sessions expire after 8 hours of inactivity
- Account lockout prevents brute-force attacks
- All sensitive actions are logged with IP addresses
- Role-based access: public users cannot update/delete cases

---

## 📸 Screenshots

See the `screenshots/` folder for 19 interface screenshots covering every feature.

---

## 👨‍💻 Project Info

**Course**: Information Systems Engineering  
**Project**: Missing Person Management System  
**Platform**: Pakistan Missing Persons Bureau  
**Year**: 2024  
