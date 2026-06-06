let allCases = [], viewMode = 'table', currentEditId = null, officers = [];

async function loadCases() {
  const status=document.getElementById('status-filter').value, priority=document.getElementById('priority-filter').value, search=document.getElementById('search-input').value;
  const res = await fetch(`/api/cases?status=${status}&priority=${priority}&search=${encodeURIComponent(search)}`);
  allCases = await res.json(); renderCases();
}
async function loadOfficers() {
  officers = await (await fetch('/api/officers')).json();
  const sel = document.getElementById('f-officer');
  if (sel) sel.innerHTML = '<option value="">Unassigned</option>' + officers.map(o=>`<option value="${o.id}">${o.name}${o.badge?' ('+o.badge+')':''}</option>`).join('');
}
function renderCases() {
  document.getElementById('results-count').textContent = `${allCases.length} case${allCases.length!==1?'s':''} found`;
  if (viewMode==='table') renderTable(); else renderCards();
}
function renderTable() {
  const tbody = document.getElementById('cases-tbody');
  if (!allCases.length) { tbody.innerHTML='<tr><td colspan="9" class="loading-cell">No cases found</td></tr>'; return; }
  tbody.innerHTML = allCases.map(c=>`<tr>
    <td><strong style="color:var(--blue-light);font-size:12px">${c.case_number}</strong></td>
    <td style="font-weight:600">${c.name}</td>
    <td style="font-size:12px;color:var(--text-muted)">${c.age||'?'} / ${c.gender||'?'}</td>
    <td style="font-size:12px;color:var(--text-muted)">${c.last_seen_location||'—'}</td>
    <td><span class="priority-pill priority-${c.priority.toLowerCase()}">${c.priority}</span></td>
    <td><span class="status-badge status-${c.status.toLowerCase()}">${c.status}</span></td>
    <td style="font-size:12px;color:var(--text-muted)">${c.assigned_officer}</td>
    <td style="font-size:12px;color:var(--text-dim)">${c.created_at.split(' ')[0]}</td>
    <td><div class="table-actions">
      <button class="action-btn" onclick="openCaseDetail(${c.id})">View</button>
      ${canEdit()?`<button class="action-btn" onclick='openCaseForm(${JSON.stringify(c)})'>Edit</button>`:''}
      ${isAdmin()?`<button class="action-btn danger" onclick="deleteCase(${c.id})">Del</button>`:''}
    </div></td>
  </tr>`).join('');
}
function renderCards() {
  const el = document.getElementById('cards-view');
  if (!allCases.length) { el.innerHTML='<div class="loading-cell">No cases found</div>'; return; }
  el.innerHTML = allCases.map(c=>`
    <div class="case-card" onclick="openCaseDetail(${c.id})">
      <div class="case-card-top"><div><div class="case-card-name">${c.name}</div><div class="case-card-num">${c.case_number}</div></div><span class="status-badge status-${c.status.toLowerCase()}">${c.status}</span></div>
      <div class="case-card-body"><div class="case-card-row">📍 ${c.last_seen_location||'Unknown'}</div><div class="case-card-row">👤 ${c.age||'?'} yrs • ${c.gender||'Unknown'}</div>${c.cnic?`<div class="case-card-row">🪪 ${c.cnic}</div>`:''}</div>
      <div class="case-card-foot"><span class="priority-pill priority-${c.priority.toLowerCase()}">${c.priority}</span><span style="font-size:11px;color:var(--text-muted)">${c.created_at.split(' ')[0]}</span></div>
    </div>`).join('');
}
function canEdit() { return ['POLICE','ADMIN','LAW_ENFORCEMENT'].includes(USER_ROLE); }
function isAdmin() { return USER_ROLE==='ADMIN'; }

function openCaseForm(data=null) {
  currentEditId = data?.id||null;
  document.getElementById('form-modal-title').textContent = data?'Edit Case':'Report Missing Person';
  document.getElementById('submit-case-btn').textContent = data?'Save Changes':'Submit Case';
  if (data) {
    ['name','age','gender','last_seen_location','description','medical_info','contact_name','contact_phone','contact_email','notes','nationality','cnic'].forEach(f=>{
      const el=document.getElementById('f-'+f.replace('_','-').replace('last-seen-location','location').replace('medical-info','medical').replace('contact-phone','contact-phone').replace('contact-email','contact-email'));
      if(el) el.value=data[f]||'';
    });
    document.getElementById('f-name').value=data.name||'';
    document.getElementById('f-age').value=data.age||'';
    document.getElementById('f-gender').value=data.gender||'';
    document.getElementById('f-location').value=data.last_seen_location||'';
    document.getElementById('f-date').value=data.last_seen_date||'';
    document.getElementById('f-desc').value=data.description||'';
    document.getElementById('f-medical').value=data.medical_info||'';
    document.getElementById('f-contact-name').value=data.contact_name||'';
    document.getElementById('f-contact-phone').value=data.contact_phone||'';
    document.getElementById('f-contact-email').value=data.contact_email||'';
    document.getElementById('f-notes').value=data.notes||'';
    document.getElementById('f-nationality').value=data.nationality||'';
    document.getElementById('f-cnic').value=data.cnic||'';
    if (canEdit()) { document.getElementById('f-priority').value=data.priority||'Medium'; document.getElementById('f-status').value=data.status||'Missing'; }
  } else { document.getElementById('case-form').reset(); }
  document.getElementById('officer-fields').style.display = canEdit()?'':'none';
  document.getElementById('note-field').style.display = canEdit()?'':'none';
  document.getElementById('case-form-modal').classList.remove('hidden');
}

document.getElementById('add-case-btn').addEventListener('click',()=>openCaseForm());
document.getElementById('close-case-form').addEventListener('click',()=>document.getElementById('case-form-modal').classList.add('hidden'));
document.getElementById('cancel-case-form').addEventListener('click',()=>document.getElementById('case-form-modal').classList.add('hidden'));

document.getElementById('case-form').addEventListener('submit', async e=>{
  e.preventDefault();
  const btn=document.getElementById('submit-case-btn'); btn.disabled=true; btn.textContent='Saving…';
  const body={
    name:document.getElementById('f-name').value, age:parseInt(document.getElementById('f-age').value)||null,
    gender:document.getElementById('f-gender').value, last_seen_location:document.getElementById('f-location').value,
    last_seen_date:document.getElementById('f-date').value, description:document.getElementById('f-desc').value,
    medical_info:document.getElementById('f-medical').value, contact_name:document.getElementById('f-contact-name').value,
    contact_phone:document.getElementById('f-contact-phone').value, contact_email:document.getElementById('f-contact-email').value,
    notes:document.getElementById('f-notes').value, nationality:document.getElementById('f-nationality').value,
    cnic:document.getElementById('f-cnic').value,
    priority:document.getElementById('f-priority')?.value||'Medium',
    status:document.getElementById('f-status')?.value||'Missing',
    assigned_officer_id:document.getElementById('f-officer')?.value||null,
    update_note:document.getElementById('f-note')?.value||'Case updated',
  };
  try {
    const url=currentEditId?`/api/cases/${currentEditId}`:'/api/cases', method=currentEditId?'PUT':'POST';
    const d=await(await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
    if (d.success) { document.getElementById('case-form-modal').classList.add('hidden'); showToast(currentEditId?'✅ Case updated':'✅ Case '+d.case_number+' filed','success'); loadCases(); }
    else showToast(d.error||'Failed','error');
  } catch { showToast('Network error','error'); }
  finally { btn.disabled=false; btn.textContent=currentEditId?'Save Changes':'Submit Case'; }
});

async function deleteCase(id) {
  if (!confirm('Delete this case permanently? This cannot be undone.')) return;
  const d=await(await fetch(`/api/cases/${id}`,{method:'DELETE'})).json();
  if(d.success){showToast('Case deleted','success');loadCases();}else showToast('Failed','error');
}

document.getElementById('view-table').addEventListener('click',()=>{viewMode='table';document.getElementById('view-table').classList.add('active');document.getElementById('view-cards').classList.remove('active');document.getElementById('table-view').classList.remove('hidden');document.getElementById('cards-view').classList.add('hidden');});
document.getElementById('view-cards').addEventListener('click',()=>{viewMode='cards';document.getElementById('view-cards').classList.add('active');document.getElementById('view-table').classList.remove('active');document.getElementById('table-view').classList.add('hidden');document.getElementById('cards-view').classList.remove('hidden');renderCards();});
document.getElementById('close-detail')?.addEventListener('click',()=>document.getElementById('case-detail-modal')?.classList.add('hidden'));

let st;
document.getElementById('search-input').addEventListener('input',()=>{clearTimeout(st);st=setTimeout(loadCases,300);});
document.getElementById('status-filter').addEventListener('change',loadCases);
document.getElementById('priority-filter').addEventListener('change',loadCases);
loadCases(); loadOfficers();
