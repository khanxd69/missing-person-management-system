from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from datetime import datetime, timedelta
from functools import wraps
import os, json, hashlib, secrets, re

# ─── APP SETUP ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mpms_secret_key_2024_$ecure!@#XYZ')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'mpms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# ─── MODELS ───────────────────────────────────────────────────

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)
    full_name     = db.Column(db.String(100))
    email         = db.Column(db.String(120), unique=True)
    badge_number  = db.Column(db.String(20))
    phone         = db.Column(db.String(20))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)
    is_active     = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until  = db.Column(db.DateTime)
    reset_token   = db.Column(db.String(200))
    reset_token_expiry = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade='all,delete')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw, method='pbkdf2:sha256:600000')

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)
        self.reset_token = hashlib.sha256(token.encode()).hexdigest()
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token):
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return self.reset_token == hashlib.sha256(token.encode()).hexdigest()


class MissingPerson(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    case_number         = db.Column(db.String(20), unique=True)
    name                = db.Column(db.String(100), nullable=False)
    age                 = db.Column(db.Integer)
    gender              = db.Column(db.String(10))
    description         = db.Column(db.Text)
    last_seen_location  = db.Column(db.String(200))
    last_seen_date      = db.Column(db.DateTime)
    medical_info        = db.Column(db.Text)
    status              = db.Column(db.String(20), default='Missing')
    priority            = db.Column(db.String(10), default='Medium')
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_by_id      = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contact_name        = db.Column(db.String(100))
    contact_phone       = db.Column(db.String(20))
    contact_email       = db.Column(db.String(120))
    notes               = db.Column(db.Text)
    nationality         = db.Column(db.String(50))
    cnic                = db.Column(db.String(20))

    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], backref='assigned_cases')
    reported_by      = db.relationship('User', foreign_keys=[reported_by_id], backref='reported_cases')
    updates          = db.relationship('CaseUpdate', backref='case', lazy=True, cascade='all,delete')
    alerts           = db.relationship('Alert', backref='case', lazy=True, cascade='all,delete')

    def to_dict(self):
        return {
            'id': self.id,
            'case_number': self.case_number,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'description': self.description,
            'last_seen_location': self.last_seen_location,
            'last_seen_date': self.last_seen_date.strftime('%Y-%m-%d') if self.last_seen_date else '',
            'medical_info': self.medical_info,
            'status': self.status,
            'priority': self.priority,
            'assigned_officer': self.assigned_officer.full_name if self.assigned_officer else 'Unassigned',
            'assigned_officer_id': self.assigned_officer_id,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'notes': self.notes,
            'nationality': self.nationality,
            'cnic': self.cnic,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else '',
            'reported_by': self.reported_by.full_name if self.reported_by else 'Unknown',
        }


class CaseUpdate(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    case_id       = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    update_text   = db.Column(db.Text)
    status_change = db.Column(db.String(50))
    timestamp     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by    = db.relationship('User', backref='case_updates')


class Alert(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    case_id     = db.Column(db.Integer, db.ForeignKey('missing_person.id'))
    alert_type  = db.Column(db.String(30))
    message     = db.Column(db.Text)
    is_active   = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_by  = db.relationship('User', backref='created_alerts')


class Notification(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title       = db.Column(db.String(120))
    message     = db.Column(db.Text)
    notif_type  = db.Column(db.String(20), default='info')
    is_read     = db.Column(db.Boolean, default=False)
    link        = db.Column(db.String(200))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notif_type,
            'is_read': self.is_read,
            'link': self.link,
            'time': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'time_ago': time_ago(self.created_at),
        }


class AuditLog(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
    action     = db.Column(db.String(100))
    details    = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship('User', backref='audit_logs')


# ─── HELPERS ──────────────────────────────────────────────────

def time_ago(dt):
    diff = datetime.utcnow() - dt
    s = diff.total_seconds()
    if s < 60: return 'just now'
    if s < 3600: return f'{int(s//60)}m ago'
    if s < 86400: return f'{int(s//3600)}h ago'
    return f'{int(s//86400)}d ago'

def generate_case_number():
    year = datetime.now().year
    count = MissingPerson.query.count() + 1
    return f"MP-{year}-{count:04d}"

def get_stats():
    total    = MissingPerson.query.count()
    missing  = MissingPerson.query.filter_by(status='Missing').count()
    located  = MissingPerson.query.filter_by(status='Located').count()
    closed   = MissingPerson.query.filter_by(status='Closed').count()
    critical = MissingPerson.query.filter_by(priority='Critical', status='Missing').count()
    alerts   = Alert.query.filter_by(is_active=True).count()
    return dict(total=total, missing=missing, located=located, closed=closed, critical=critical, active_alerts=alerts)

def notify_all_officers(title, message, notif_type='info', link=None, exclude_id=None):
    officers = User.query.filter(
        User.role.in_(['POLICE', 'LAW_ENFORCEMENT', 'ADMIN']),
        User.is_active == True
    ).all()
    for u in officers:
        if exclude_id and u.id == exclude_id:
            continue
        n = Notification(user_id=u.id, title=title, message=message, notif_type=notif_type, link=link)
        db.session.add(n)

def notify_user(user_id, title, message, notif_type='info', link=None):
    n = Notification(user_id=user_id, title=title, message=message, notif_type=notif_type, link=link)
    db.session.add(n)

def audit(action, details=''):
    if 'user_id' in session:
        log = AuditLog(
            user_id=session['user_id'],
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)

def validate_password(pw):
    if len(pw) < 8: return 'Password must be at least 8 characters'
    if not re.search(r'[A-Z]', pw): return 'Password must contain an uppercase letter'
    if not re.search(r'[a-z]', pw): return 'Password must contain a lowercase letter'
    if not re.search(r'\d', pw): return 'Password must contain a number'
    return None


# ─── AUTH DECORATORS ──────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def dec(*a, **kw):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*a, **kw)
        return dec
    return decorator


# ─── AUTH ROUTES ──────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        d = request.get_json()
        username = (d.get('username') or '').strip()
        password = (d.get('password') or '').strip()
        role     = (d.get('role') or '').strip()

        user = User.query.filter_by(username=username).first()

        if not user or not user.is_active:
            return jsonify({'success': False, 'message': 'Invalid credentials or account disabled'}), 401

        if user.is_locked():
            remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            return jsonify({'success': False, 'message': f'Account locked. Try again in {remaining} minute(s)'}), 403

        if user.role != role:
            return jsonify({'success': False, 'message': 'Selected role does not match account'}), 401

        if not user.check_password(password):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                notify_user(user.id, '⚠️ Account Locked',
                    f'Your account was locked after 5 failed login attempts. Try again in 15 minutes.',
                    'warning')
                db.session.commit()
                return jsonify({'success': False, 'message': 'Too many failed attempts. Account locked for 15 minutes.'}), 403
            db.session.commit()
            remaining = 5 - user.failed_attempts
            return jsonify({'success': False, 'message': f'Wrong password. {remaining} attempt(s) left.'}), 401

        user.failed_attempts = 0
        user.locked_until    = None
        user.last_login      = datetime.utcnow()
        db.session.commit()

        session.permanent = True
        session['user_id']   = user.id
        session['username']  = user.username
        session['role']      = user.role
        session['full_name'] = user.full_name or user.username

        audit('LOGIN', f'User {username} logged in as {role}')
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('dashboard')})

    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        audit('LOGOUT', f"User {session.get('username')} logged out")
        try: db.session.commit()
        except: db.session.rollback()
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        d = request.get_json()
        email = (d.get('email') or '').strip().lower()
        user = User.query.filter(db.func.lower(User.email) == email).first()

        # Always return success (security: don't reveal if email exists)
        if user and user.is_active:
            token = user.generate_reset_token()
            db.session.commit()
            # In production send email; here we return the token directly for demo
            reset_link = url_for('reset_password', token=token, _external=True)
            notify_user(user.id, '🔑 Password Reset Requested',
                f'A password reset was requested for your account. Use the link in the reset page.',
                'warning')
            db.session.commit()
            return jsonify({'success': True, 'reset_link': reset_link, 'demo': True})

        return jsonify({'success': True})  # same response either way

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        d = request.get_json()
        new_pw  = d.get('password', '')
        confirm = d.get('confirm', '')

        if new_pw != confirm:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

        err = validate_password(new_pw)
        if err:
            return jsonify({'success': False, 'message': err}), 400

        # Find user by token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = User.query.filter_by(reset_token=token_hash).first()

        if not user or not user.verify_reset_token(token):
            return jsonify({'success': False, 'message': 'Reset link is invalid or has expired'}), 400

        user.set_password(new_pw)
        user.reset_token        = None
        user.reset_token_expiry = None
        user.failed_attempts    = 0
        user.locked_until       = None
        notify_user(user.id, '✅ Password Changed',
            'Your password was successfully reset. If this was not you, contact admin immediately.',
            'success')
        db.session.commit()

        audit('PASSWORD_RESET', f'Password reset for user {user.username}')
        db.session.commit()
        return jsonify({'success': True})

    # Validate token on GET
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = User.query.filter_by(reset_token=token_hash).first()
    valid = user and user.verify_reset_token(token)
    return render_template('reset_password.html', token=token, valid=valid)

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    d = request.get_json()
    user = User.query.get(session['user_id'])

    if not user.check_password(d.get('current_password', '')):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

    err = validate_password(d.get('new_password', ''))
    if err:
        return jsonify({'success': False, 'message': err}), 400

    if d.get('new_password') != d.get('confirm_password'):
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    user.set_password(d['new_password'])
    notify_user(user.id, '🔒 Password Changed', 'Your password was changed successfully.', 'success')
    db.session.commit()
    audit('CHANGE_PASSWORD', 'User changed their password')
    db.session.commit()
    return jsonify({'success': True})


# ─── MAIN PAGES ───────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    stats  = get_stats()
    recent = MissingPerson.query.order_by(MissingPerson.created_at.desc()).limit(5).all()
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(3).all()
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('dashboard.html', stats=stats, recent=recent, alerts=alerts, unread=unread)

@app.route('/cases')
@login_required
def cases():
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('cases.html', unread=unread)

@app.route('/alerts')
@login_required
def alerts_page():
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('alerts.html', unread=unread)

@app.route('/users')
@login_required
def users_page():
    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('users.html', unread=unread)

@app.route('/profile')
@login_required
def profile():
    user   = User.query.get(session['user_id'])
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    logs   = AuditLog.query.filter_by(user_id=session['user_id']).order_by(AuditLog.timestamp.desc()).limit(10).all()
    return render_template('profile.html', user=user, logs=logs, unread=unread)

@app.route('/audit')
@login_required
@role_required('ADMIN')
def audit_page():
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return render_template('audit.html', unread=unread)


# ─── CASES API ────────────────────────────────────────────────

@app.route('/api/cases')
@login_required
def api_cases():
    status   = request.args.get('status', '')
    priority = request.args.get('priority', '')
    search   = request.args.get('search', '')
    q = MissingPerson.query
    if status:   q = q.filter_by(status=status)
    if priority: q = q.filter_by(priority=priority)
    if search:
        q = q.filter(db.or_(
            MissingPerson.name.ilike(f'%{search}%'),
            MissingPerson.case_number.ilike(f'%{search}%'),
            MissingPerson.last_seen_location.ilike(f'%{search}%'),
            MissingPerson.cnic.ilike(f'%{search}%'),
        ))
    results = q.order_by(MissingPerson.created_at.desc()).all()
    return jsonify([c.to_dict() for c in results])

@app.route('/api/cases/<int:case_id>')
@login_required
def api_case_detail(case_id):
    c    = MissingPerson.query.get_or_404(case_id)
    data = c.to_dict()
    data['updates'] = [{
        'text': u.update_text,
        'status_change': u.status_change,
        'by': u.updated_by.full_name if u.updated_by else 'System',
        'role': u.updated_by.role if u.updated_by else '',
        'time': u.timestamp.strftime('%Y-%m-%d %H:%M'),
        'ago': time_ago(u.timestamp),
    } for u in sorted(c.updates, key=lambda x: x.timestamp, reverse=True)]
    return jsonify(data)

@app.route('/api/cases', methods=['POST'])
@login_required
def api_create_case():
    d = request.get_json()
    last_seen_date = None
    if d.get('last_seen_date'):
        try: last_seen_date = datetime.strptime(d['last_seen_date'], '%Y-%m-%d')
        except: pass

    c = MissingPerson(
        case_number        = generate_case_number(),
        name               = d['name'],
        age                = d.get('age') or None,
        gender             = d.get('gender'),
        description        = d.get('description'),
        last_seen_location = d.get('last_seen_location'),
        last_seen_date     = last_seen_date,
        medical_info       = d.get('medical_info'),
        priority           = d.get('priority', 'Medium'),
        contact_name       = d.get('contact_name'),
        contact_phone      = d.get('contact_phone'),
        contact_email      = d.get('contact_email'),
        notes              = d.get('notes'),
        nationality        = d.get('nationality'),
        cnic               = d.get('cnic'),
        reported_by_id     = session['user_id'],
        status             = 'Missing',
    )
    db.session.add(c)
    db.session.flush()

    db.session.add(CaseUpdate(
        case_id=c.id, updated_by_id=session['user_id'],
        update_text=f"Case filed by {session['full_name']}",
        status_change='Missing'
    ))

    # Notify officers
    notify_all_officers(
        '🔔 New Missing Person Case',
        f"Case {c.case_number} filed: {c.name}, {c.age or '?'} yrs, last seen at {c.last_seen_location or 'unknown'}.",
        'warning',
        link='/cases',
        exclude_id=session['user_id']
    )

    audit('CREATE_CASE', f'Created case {c.case_number} for {c.name}')
    db.session.commit()
    return jsonify({'success': True, 'case_number': c.case_number, 'id': c.id})

@app.route('/api/cases/<int:case_id>', methods=['PUT'])
@login_required
@role_required('POLICE', 'ADMIN', 'LAW_ENFORCEMENT')
def api_update_case(case_id):
    c  = MissingPerson.query.get_or_404(case_id)
    d  = request.get_json()
    old_status = c.status

    fields = ['name','age','gender','description','last_seen_location','medical_info',
              'status','priority','contact_name','contact_phone','contact_email','notes','nationality','cnic']
    for f in fields:
        if f in d:
            setattr(c, f, d[f] or None if f == 'age' else d[f])

    if 'assigned_officer_id' in d:
        c.assigned_officer_id = d['assigned_officer_id'] or None

    if d.get('last_seen_date'):
        try: c.last_seen_date = datetime.strptime(d['last_seen_date'], '%Y-%m-%d')
        except: pass

    c.updated_at = datetime.utcnow()

    note = d.get('update_note', 'Case updated')
    status_change = f"{old_status} → {c.status}" if old_status != c.status else None

    db.session.add(CaseUpdate(
        case_id=c.id, updated_by_id=session['user_id'],
        update_text=note, status_change=status_change
    ))

    # Notify relevant parties on status change
    if status_change:
        notify_all_officers(
            f'📋 Case Status Changed: {c.case_number}',
            f"{c.name}'s case status changed: {status_change}",
            'success' if c.status == 'Located' else 'info',
            link='/cases'
        )
        if c.status == 'Located':
            notify_user(c.reported_by_id, f'✅ Person Found: {c.name}',
                f"Great news! {c.name} (Case {c.case_number}) has been located.",
                'success', link='/cases')

    audit('UPDATE_CASE', f'Updated case {c.case_number}: {note}')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/cases/<int:case_id>', methods=['DELETE'])
@login_required
@role_required('ADMIN')
def api_delete_case(case_id):
    c = MissingPerson.query.get_or_404(case_id)
    cn = c.case_number
    db.session.delete(c)
    audit('DELETE_CASE', f'Deleted case {cn}')
    db.session.commit()
    return jsonify({'success': True})


# ─── ALERTS API ───────────────────────────────────────────────

@app.route('/api/alerts')
@login_required
def api_get_alerts():
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).all()
    return jsonify([{
        'id': a.id, 'alert_type': a.alert_type, 'message': a.message,
        'case_number': a.case.case_number if a.case else '',
        'case_name': a.case.name if a.case else '',
        'case_id': a.case_id,
        'created_by': a.created_by.full_name if a.created_by else 'System',
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
    } for a in alerts])

@app.route('/api/alerts', methods=['POST'])
@login_required
@role_required('POLICE', 'ADMIN', 'LAW_ENFORCEMENT')
def api_create_alert():
    d = request.get_json()
    a = Alert(case_id=d['case_id'], alert_type=d['alert_type'],
              message=d['message'], created_by_id=session['user_id'])
    db.session.add(a)
    db.session.flush()

    notify_all_officers(
        f'🚨 {d["alert_type"]} ALERT Issued',
        d['message'], 'danger', link='/alerts'
    )
    audit('CREATE_ALERT', f'{d["alert_type"]} alert for case_id {d["case_id"]}')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@login_required
@role_required('POLICE', 'ADMIN', 'LAW_ENFORCEMENT')
def api_dismiss_alert(alert_id):
    a = Alert.query.get_or_404(alert_id)
    a.is_active = False
    audit('DISMISS_ALERT', f'Dismissed alert {alert_id}')
    db.session.commit()
    return jsonify({'success': True})


# ─── NOTIFICATIONS API ────────────────────────────────────────

@app.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(user_id=session['user_id'])\
        .order_by(Notification.created_at.desc()).limit(20).all()
    unread = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return jsonify({'notifications': [n.to_dict() for n in notifs], 'unread': unread})

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_read_all_notifs():
    Notification.query.filter_by(user_id=session['user_id'], is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/notifications/<int:nid>/read', methods=['POST'])
@login_required
def api_read_notif(nid):
    n = Notification.query.filter_by(id=nid, user_id=session['user_id']).first_or_404()
    n.is_read = True
    db.session.commit()
    return jsonify({'success': True})


# ─── USERS API ────────────────────────────────────────────────

@app.route('/api/officers')
@login_required
def api_officers():
    officers = User.query.filter(User.role.in_(['POLICE', 'LAW_ENFORCEMENT']), User.is_active == True).all()
    return jsonify([{'id': u.id, 'name': u.full_name or u.username, 'badge': u.badge_number} for u in officers])

@app.route('/api/users')
@login_required
@role_required('ADMIN')
def api_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id, 'username': u.username, 'full_name': u.full_name,
        'role': u.role, 'email': u.email, 'badge_number': u.badge_number,
        'phone': u.phone, 'is_active': u.is_active,
        'last_login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Never',
        'created_at': u.created_at.strftime('%Y-%m-%d'),
        'is_locked': u.is_locked(),
    } for u in users])

@app.route('/api/users', methods=['POST'])
@login_required
@role_required('ADMIN')
def api_create_user():
    d = request.get_json()
    if User.query.filter_by(username=d['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if d.get('email') and User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email already in use'}), 400
    err = validate_password(d.get('password', ''))
    if err: return jsonify({'error': err}), 400

    u = User(username=d['username'], role=d['role'], full_name=d.get('full_name'),
             email=d.get('email'), badge_number=d.get('badge_number'), phone=d.get('phone'))
    u.set_password(d['password'])
    db.session.add(u)
    db.session.flush()
    notify_user(u.id, '👋 Welcome to MPMS',
        f'Your account has been created. Username: {u.username} | Role: {u.role}', 'success')
    audit('CREATE_USER', f'Created user {d["username"]} with role {d["role"]}')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required('ADMIN')
def api_update_user(user_id):
    u = User.query.get_or_404(user_id)
    d = request.get_json()
    for f in ['full_name', 'email', 'badge_number', 'phone', 'is_active']:
        if f in d: setattr(u, f, d[f])
    if d.get('password'):
        err = validate_password(d['password'])
        if err: return jsonify({'error': err}), 400
        u.set_password(d['password'])
        notify_user(u.id, '🔒 Password Updated',
            'Your password was changed by an administrator.', 'warning')
    if 'unlock' in d and d['unlock']:
        u.failed_attempts = 0
        u.locked_until    = None
        notify_user(u.id, '🔓 Account Unlocked', 'Your account has been unlocked.', 'success')
    audit('UPDATE_USER', f'Updated user {u.username}')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('ADMIN')
def api_delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    u = User.query.get_or_404(user_id)
    uname = u.username
    db.session.delete(u)
    audit('DELETE_USER', f'Deleted user {uname}')
    db.session.commit()
    return jsonify({'success': True})


# ─── STATS & CHARTS ───────────────────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify(get_stats())

@app.route('/api/chart/monthly')
@login_required
def api_monthly_chart():
    data = []
    for i in range(6):
        base  = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month = base - timedelta(days=30 * i)
        count = MissingPerson.query.filter(
            db.extract('month', MissingPerson.created_at) == month.month,
            db.extract('year',  MissingPerson.created_at) == month.year
        ).count()
        data.append({'month': month.strftime('%b %Y'), 'count': count})
    return jsonify(list(reversed(data)))

@app.route('/api/audit-logs')
@login_required
@role_required('ADMIN')
def api_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': l.id,
        'user': l.user.username if l.user else 'Unknown',
        'action': l.action,
        'details': l.details,
        'ip': l.ip_address,
        'time': l.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    } for l in logs])


# ─── DB INIT ──────────────────────────────────────────────────

def init_db():
    db.create_all()
    if User.query.first(): return

    seed_users = [
        ('admin1',   'Admin@123',  'ADMIN',           'Admin Hassan',    'admin@mpms.gov.pk',    None,    None),
        ('officer1', 'Police@123', 'POLICE',           'Officer Ahmed Khan','ahmed@mpms.gov.pk', 'P-001', '0300-1234001'),
        ('officer2', 'Police@456', 'POLICE',           'Officer Sara Malik','sara@mpms.gov.pk',  'P-002', '0300-1234002'),
        ('law1',     'Law@123',    'LAW_ENFORCEMENT',  'Inspector Bilal', 'bilal@mpms.gov.pk',   'LE-001','0300-1234003'),
        ('law2',     'Law@456',    'LAW_ENFORCEMENT',  'Inspector Nida',  'nida@mpms.gov.pk',    'LE-002','0300-1234004'),
        ('public1',  'Public@123', 'PUBLIC',           'Ali Raza',        'ali@email.com',       None,    '0311-1234567'),
        ('public2',  'Public@456', 'PUBLIC',           'Fatima Malik',    'fatima@email.com',    None,    '0322-7654321'),
    ]
    users = {}
    for uname, pw, role, name, email, badge, phone in seed_users:
        u = User(username=uname, role=role, full_name=name, email=email,
                 badge_number=badge, phone=phone)
        u.set_password(pw)
        db.session.add(u)
        db.session.flush()
        users[uname] = u

    sample_cases = [
        ('Zara Khan',     8,  'Female', 'Child, black hair, pink dress, school bag',          'F-7 Markaz, Islamabad',       'Missing','Critical','officer1','42501-1234567-8'),
        ('Usman Ali',     45, 'Male',   'Tall, beard, blue shirt, white shalwar kameez',       'Saddar, Rawalpindi',          'Missing','High',    'officer1','35202-9876543-1'),
        ('Maria Bibi',    22, 'Female', 'College student, glasses, purple dupatta',            'Gulberg, Lahore',             'Located','Medium',  'officer2','35201-5555555-2'),
        ('Hassan Raza',   67, 'Male',   'Elderly, grey beard, diabetes patient, hearing aid',  'Clifton, Karachi',            'Missing','High',    'law1',    '42201-1111111-3'),
        ('Nadia Iqbal',   15, 'Female', 'Teenager, school uniform, white hijab',               'Liberty Market, Lahore',     'Missing','Critical','officer2','35201-2222222-4'),
        ('Tariq Mahmood', 38, 'Male',   'Medium build, working clothes, factory worker',       'Korangi Industrial, Karachi', 'Closed', 'Low',    'law2',    '42301-3333333-5'),
        ('Sana Butt',     28, 'Female', 'Nurse uniform, last seen after night shift',          'Services Hospital, Lahore',   'Missing','High',    'officer1','35201-4444444-6'),
    ]
    admin = users['admin1']
    for i, (name, age, gender, desc, loc, status, priority, officer, cnic) in enumerate(sample_cases):
        c = MissingPerson(
            case_number        = f"MP-2024-{i+1:04d}",
            name=name, age=age, gender=gender, description=desc,
            last_seen_location = loc, status=status, priority=priority,
            reported_by_id     = admin.id,
            assigned_officer_id= users[officer].id,
            last_seen_date     = datetime.now() - timedelta(days=(i+1)*4),
            contact_name       = 'Family Contact', contact_phone='0300-0000000',
            contact_email      = 'contact@example.com',
            nationality        = 'Pakistani', cnic=cnic,
        )
        db.session.add(c)
        db.session.flush()
        db.session.add(CaseUpdate(case_id=c.id, updated_by_id=admin.id,
                                   update_text='Case filed in the system', status_change=status))

    db.session.add(Alert(case_id=1, alert_type='AMBER',
        message='AMBER ALERT: 8-year-old girl Zara Khan missing from F-7 Markaz, Islamabad. Last seen wearing pink dress at 3 PM.',
        created_by_id=users['admin1'].id))
    db.session.add(Alert(case_id=4, alert_type='SILVER',
        message='SILVER ALERT: Elderly male Hassan Raza (67) with diabetes missing from Clifton, Karachi. May be disoriented.',
        created_by_id=users['admin1'].id))
    db.session.add(Alert(case_id=5, alert_type='CRITICAL',
        message='CRITICAL: Missing teenager Nadia Iqbal (15). Last seen Liberty Market. Possible abduction.',
        created_by_id=users['admin1'].id))

    # Welcome notifications
    for uname, u in users.items():
        db.session.add(Notification(user_id=u.id, title='👋 Welcome to MPMS',
            message=f'Welcome {u.full_name}! Your account is ready. Role: {u.role}',
            notif_type='success'))
    db.session.commit()
    print("✅ Database initialized with sample data!")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
