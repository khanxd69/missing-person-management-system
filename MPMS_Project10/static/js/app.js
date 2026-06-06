// ── Live clock ─────────────────────────────────────────
const clock = document.getElementById('live-time');
if (clock) { const tick = () => clock.textContent = new Date().toLocaleString('en-PK',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); tick(); setInterval(tick,1000); }

// ── Sidebar toggle ──────────────────────────────────────
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
if (sidebarToggle) sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
document.addEventListener('click', e => {
  if (sidebar && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) sidebar.classList.remove('open');
});

// ── Toast ───────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity='0'; t.style.transform='translateX(30px)'; setTimeout(()=>t.remove(),300); }, 3500);
}

// ── Notifications ───────────────────────────────────────
async function loadNotifications() {
  try {
    const res = await fetch('/api/notifications');
    const d   = await res.json();
    const badge = document.getElementById('notif-count');
    if (badge) {
      badge.textContent = d.unread;
      badge.style.display = d.unread > 0 ? 'flex' : 'none';
    }
    const list = document.getElementById('notif-list');
    if (!list) return;
    if (!d.notifications.length) {
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">No notifications</div>';
      return;
    }
    list.innerHTML = d.notifications.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'notif-unread'}" data-id="${n.id}" onclick="readNotif(${n.id}, this, '${n.link||''}')">
        <div class="notif-icon notif-${n.type}"></div>
        <div class="notif-body">
          <div class="notif-title">${n.title}</div>
          <div class="notif-msg">${n.message}</div>
          <div class="notif-time">${n.time_ago}</div>
        </div>
      </div>`).join('');
  } catch(e) {}
}

async function readNotif(id, el, link) {
  await fetch(`/api/notifications/${id}/read`, {method:'POST'});
  el.classList.remove('notif-unread');
  loadNotifications();
  if (link && link !== 'None') window.location.href = link;
}

document.getElementById('mark-all-read')?.addEventListener('click', async () => {
  await fetch('/api/notifications/read-all', {method:'POST'});
  loadNotifications();
  showToast('All notifications marked as read');
});

const bell = document.getElementById('notif-bell');
const dropdown = document.getElementById('notif-dropdown');
if (bell && dropdown) {
  bell.addEventListener('click', e => { e.stopPropagation(); dropdown.classList.toggle('hidden'); if (!dropdown.classList.contains('hidden')) loadNotifications(); });
  document.addEventListener('click', e => { if (!document.getElementById('notif-wrap')?.contains(e.target)) dropdown?.classList.add('hidden'); });
}

loadNotifications();
setInterval(loadNotifications, 30000);

// ── Case Detail Modal ───────────────────────────────────
async function openCaseDetail(caseId) {
  const overlay  = document.getElementById('case-detail-modal');
  const content  = document.getElementById('case-detail-content');
  if (!overlay) return;
  overlay.classList.remove('hidden');
  content.innerHTML = '<div class="loading-state">Loading…</div>';
  try {
    const d = await (await fetch(`/api/cases/${caseId}`)).json();
    document.getElementById('detail-case-number').textContent = d.case_number;
    document.getElementById('detail-case-name').textContent   = d.name;
    const editBtn = document.getElementById('edit-case-btn');
    if (editBtn) editBtn.onclick = () => { overlay.classList.add('hidden'); if(typeof openCaseForm==='function') openCaseForm(d); };
    content.innerHTML = `
      <div class="detail-grid">
        <div>
          <div class="detail-section"><h4>Person Information</h4>
            ${row('Full Name', d.name)} ${row('Age', d.age||'—')} ${row('Gender', d.gender||'—')}
            ${row('Nationality', d.nationality||'—')} ${row('CNIC', d.cnic||'—')}
            ${row('Description', d.description||'—')} ${row('Medical Info', d.medical_info||'—')}
          </div>
          <div class="detail-section"><h4>Contact Details</h4>
            ${row('Contact Name', d.contact_name||'—')} ${row('Phone', d.contact_phone||'—')} ${row('Email', d.contact_email||'—')}
          </div>
        </div>
        <div>
          <div class="detail-section"><h4>Case Details</h4>
            ${row('Case #', d.case_number)}
            ${row('Status', `<span class="status-badge status-${d.status.toLowerCase()}">${d.status}</span>`)}
            ${row('Priority', `<span class="priority-pill priority-${d.priority.toLowerCase()}">${d.priority}</span>`)}
            ${row('Last Seen', d.last_seen_location||'—')} ${row('Date', d.last_seen_date||'—')}
            ${row('Assigned Officer', d.assigned_officer)} ${row('Reported By', d.reported_by)}
            ${row('Filed', d.created_at)} ${row('Updated', d.updated_at)}
          </div>
          <div class="detail-section"><h4>📋 Case Timeline</h4>
            <div class="updates-list">
              ${d.updates.length ? d.updates.map(u=>`
                <div class="update-item">
                  <div class="update-header"><span class="update-by">${u.by}</span><span class="update-time">${u.ago}</span></div>
                  <div class="update-text">${u.text}</div>
                  ${u.status_change?`<div class="update-change">↪ ${u.status_change}</div>`:''}
                </div>`).join('') : '<div class="empty-state-sm">No updates</div>'}
            </div>
          </div>
        </div>
      </div>`;
  } catch { content.innerHTML = '<div class="empty-state-sm">Failed to load</div>'; }
}
function row(label, val) { return `<div class="detail-row"><span class="detail-label">${label}</span><span class="detail-value">${val}</span></div>`; }

document.addEventListener('click', e => {
  const overlay = document.getElementById('case-detail-modal');
  if (overlay && e.target === overlay) overlay.classList.add('hidden');
});
document.getElementById('close-detail')?.addEventListener('click', () => document.getElementById('case-detail-modal')?.classList.add('hidden'));
