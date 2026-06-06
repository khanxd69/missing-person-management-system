# 🛠 MPMS Developer & Deployment Guide
## How Everything Works — Complete Technical Reference

---

## Part 1: What Technologies Were Used & Why

### Backend: Python + Flask
Flask is a lightweight Python web framework. We chose it because:
- Simple to set up: `python app.py` is all it takes
- Built-in routing, sessions, templating (Jinja2)
- Huge ecosystem of extensions

**Key Flask concepts used:**
```python
@app.route('/cases')          # URL routing
@login_required               # Custom decorator for auth
render_template('cases.html') # Jinja2 HTML rendering
session['user_id']            # Server-side session storage
jsonify(data)                 # Return JSON for API calls
request.get_json()            # Read incoming JSON body
```

### Database: SQLite + SQLAlchemy ORM
SQLite is a file-based database — zero setup, perfect for learning and small deployments.
SQLAlchemy ORM lets you write Python classes instead of SQL:

```python
# Define a table as a Python class
class MissingPerson(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # ...

# Query like Python, not SQL
cases = MissingPerson.query.filter_by(status='Missing').all()

# Create a record
new_case = MissingPerson(name='John', status='Missing')
db.session.add(new_case)
db.session.commit()
```

### Password Security: Werkzeug + PBKDF2-SHA256
Never store plain text passwords. Werkzeug handles hashing:

```python
from werkzeug.security import generate_password_hash, check_password_hash

# When user sets password (one-way hash):
user.password_hash = generate_password_hash('MyPassword@123',
    method='pbkdf2:sha256:600000')  # 600,000 iterations

# When user logs in (compare):
is_correct = check_password_hash(user.password_hash, 'MyPassword@123')
# Returns True/False — original password is never recoverable
```

**Why PBKDF2?** It's deliberately slow (600,000 rounds), making brute-force attacks take years instead of seconds.

### Password Reset: itsdangerous + SHA-256
Reset flow uses two-layer security:
```python
import secrets, hashlib

# 1. Generate a cryptographically random token (sent to user)
raw_token = secrets.token_urlsafe(32)  # e.g. "k3mX9..."

# 2. Hash it before storing (so DB breach doesn't leak tokens)
stored_hash = hashlib.sha256(raw_token.encode()).hexdigest()
user.reset_token = stored_hash
user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)

# 3. Verify: hash the submitted token, compare to stored hash
submitted_hash = hashlib.sha256(submitted_token.encode()).hexdigest()
is_valid = (submitted_hash == user.reset_token)
```

### Frontend: Vanilla HTML/CSS/JavaScript
No React or Vue — just clean HTML, CSS variables, and ES6 JavaScript.

**Why?**
- Zero build step — open the file, it works
- Easier to understand and modify
- Chart.js loaded from CDN for charts

**Key JS patterns used:**
```javascript
// Fetch API for AJAX calls (no jQuery needed)
const res = await fetch('/api/cases', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'John', age: 25})
});
const data = await res.json();

// Dynamic HTML rendering
tbody.innerHTML = cases.map(c => `
  <tr><td>${c.name}</td><td>${c.status}</td></tr>
`).join('');
```

**CSS Variables** for consistent theming:
```css
:root {
  --red: #e63946;       /* Primary accent */
  --bg: #0d1117;        /* Page background */
  --bg2: #161b22;       /* Card background */
  --text: #e6edf3;      /* Primary text */
}
/* Usage: */
.btn { background: var(--red); }
```

---

## Part 2: How the Application Works (Request Flow)

### A Request's Journey:

```
1. User types http://localhost:5000/cases in browser
2. Browser sends: GET /cases HTTP/1.1
3. Flask matches route: @app.route('/cases')
4. Decorator checks: is user_id in session?
   → No: redirect to /login
   → Yes: continue
5. Function runs: render_template('cases.html', unread=5)
6. Jinja2 fills in {{ session.full_name }}, {{ unread }}, etc.
7. Browser receives completed HTML
8. Browser loads /static/css/main.css and /static/js/cases.js
9. cases.js runs: fetch('/api/cases') → gets JSON → builds table
10. User sees the page with live data
```

### Authentication Flow:
```
Login form submitted
→ POST /login with JSON {username, password, role}
→ Flask finds user in DB
→ Checks: is account active? not locked? role matches?
→ Werkzeug compares password hash
→ On success: session['user_id'] = user.id (stored server-side)
→ On failure: increment failed_attempts, lock if ≥ 5
→ Return JSON {success: true, redirect: '/dashboard'}
→ JS redirects browser
```

### Session Management:
Flask stores session data in a signed cookie (using SECRET_KEY). The cookie contains the session ID, not the actual data. Data lives on the server for 8 hours.

---

## Part 3: File-by-File Explanation

### `app.py` — The Heart
```
Models (lines 1-130):    6 database tables defined as Python classes
Auth Routes (131-280):   login, logout, forgot/reset/change password
Page Routes (281-330):   dashboard, cases, alerts, users, profile, audit
Cases API (331-440):     GET/POST/PUT/DELETE /api/cases
Alerts API (441-490):    GET/POST /api/alerts, dismiss
Notifs API (491-530):    GET/POST notifications
Users API (531-610):     Admin CRUD for users
Stats/Charts (611-650):  Stats endpoint, monthly chart data
DB Init (651-720):       Create tables + seed sample data
```

### `templates/base.html` — Layout Shell
Every page extends this. Contains:
- Sidebar with navigation links (role-conditional)
- Top bar with clock, notification bell, user name
- JavaScript includes
- Toast container div

### `static/js/app.js` — Shared Utilities
Loaded on every page. Provides:
- `showToast(msg, type)` — floating notification
- `loadNotifications()` — fetches and renders bell notifications
- `openCaseDetail(id)` — modal with full case + timeline
- Live clock updater
- Sidebar toggle for mobile

---

## Part 4: Running the App — Step by Step

### First Time Setup
```bash
# 1. Make sure Python 3.10+ is installed
python --version

# 2. Navigate to project folder
cd missing_persons_system

# 3. (Optional but recommended) Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
python app.py
```

**What happens on first run:**
```
app.py starts
→ Flask initializes
→ init_db() is called
→ SQLite file created: database/mpms.db
→ 6 database tables created
→ 7 sample users inserted
→ 7 sample cases inserted
→ 3 alerts inserted
→ Welcome notifications sent
→ "✅ Database initialized!" printed
→ Server starts on http://localhost:5000
```

### Subsequent Runs
Just `python app.py` — database already exists, init_db skips seeding.

---

## Part 5: Deployment — Every Option Explained

### Option A: Local Network (Share with teammates)
```bash
# Change this in app.py at the bottom:
app.run(debug=False, host='0.0.0.0', port=5000)

# Run it
python app.py

# Others on the same WiFi can access at:
# http://YOUR_LOCAL_IP:5000
# Find your IP: ipconfig (Windows) or ifconfig (Mac/Linux)
```

### Option B: Gunicorn (Production-grade, Linux/Mac)
```bash
pip install gunicorn

# 4 workers = handles 4 requests simultaneously
gunicorn app:app -w 4 -b 0.0.0.0:8000

# With logging:
gunicorn app:app -w 4 -b 0.0.0.0:8000 --access-logfile access.log --error-logfile error.log
```

### Option C: Docker
```dockerfile
# Create Dockerfile in project root:
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
RUN mkdir -p database
EXPOSE 8000
CMD ["gunicorn", "app:app", "-w", "2", "-b", "0.0.0.0:8000"]
```
```bash
# Build and run:
docker build -t mpms-app .
docker run -d -p 8000:8000 -v $(pwd)/database:/app/database --name mpms mpms-app

# Access at http://localhost:8000
# View logs: docker logs mpms
# Stop: docker stop mpms
```

### Option D: PythonAnywhere (Free, No Credit Card)
1. Go to **pythonanywhere.com** → sign up free
2. Go to **Files** tab → upload your project zip
3. Open **Bash console**:
   ```bash
   unzip missing_persons_system_v2.zip
   cd missing_persons_system
   pip3.11 install --user flask flask-sqlalchemy werkzeug itsdangerous
   ```
4. Go to **Web** tab → Add a new web app
5. Choose **Manual configuration** → Python 3.11
6. Set **Source code**: `/home/YOURNAME/missing_persons_system`
7. Edit **WSGI configuration file**, replace content with:
   ```python
   import sys
   sys.path.insert(0, '/home/YOURNAME/missing_persons_system')
   from app import app as application
   with application.app_context():
       from app import init_db; init_db()
   ```
8. Click **Reload** → Visit `YOURNAME.pythonanywhere.com` 🎉

### Option E: Render.com (Free, Auto-Deploy from GitHub)
1. Push code to GitHub
2. Go to **render.com** → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add env variable: `SECRET_KEY` = your long random string
5. Deploy → Your app gets a live URL

### Option F: Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Your app is live in ~2 minutes
```

---

## Part 6: Environment Variables (Production Security)

```bash
# Never commit your real SECRET_KEY to GitHub!
# Set environment variables instead:

# Linux/Mac:
export SECRET_KEY="super-long-random-string-at-least-32-chars"

# Windows:
set SECRET_KEY=super-long-random-string-at-least-32-chars

# Or create a .env file (add .env to .gitignore):
echo "SECRET_KEY=your-random-key-here" > .env

# Generate a secure key:
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Part 7: Switching to PostgreSQL (Production Scale)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# In app.py, replace the SQLite URI:
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://username:password@localhost:5432/mpms_db'

# Create the database:
psql -U postgres
CREATE DATABASE mpms_db;
\q

# Run app — SQLAlchemy creates all tables automatically
python app.py
```

---

## Part 8: Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: flask` | Run `pip install flask flask-sqlalchemy werkzeug itsdangerous` |
| `Address already in use` | Another process uses port 5000. Run: `fuser -k 5000/tcp` or change port |
| `Database locked` | Another app.py is already running. Kill it: `pkill -f app.py` |
| Login not working | Check role matches (Admin needs ADMIN role selected) |
| No notifications | Check browser console for JS errors |
| Charts not loading | Check internet connection (Chart.js loads from CDN) |
| Can't delete case | Only Admin role can delete. Police can only update |

---

## Part 9: Default Accounts & Testing

```
ADMIN:           admin1 / Admin@123
POLICE:          officer1 / Police@123
                 officer2 / Police@456  
LAW ENFORCEMENT: law1 / Law@123
                 law2 / Law@456
PUBLIC:          public1 / Public@123
                 public2 / Public@456
```

**Test the lockout:**
1. Login as `admin1` with wrong password 5 times
2. Account locks for 15 minutes
3. As `admin1` (another session), go to Users → Edit → Unlock Account

**Test forgot password:**
1. Click "Forgot password?" on login page
2. Enter `admin@mpms.gov.pk`
3. Copy the reset link shown (demo mode)
4. Open the link and set a new password

---

## Part 10: Project Statistics

| Metric | Value |
|--------|-------|
| Total Python lines | ~860 |
| Total HTML templates | 10 files |
| Total CSS lines | ~650 |
| Total JS lines | ~500 |
| Database tables | 6 |
| API endpoints | 21 |
| UI screenshots | 19 |
| Roles supported | 4 |
| Sample data | 7 users, 7+ cases, 3 alerts |
