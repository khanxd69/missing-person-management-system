let selAlertType='AMBER';
async function renderAlerts() {
  const container=document.getElementById('alerts-container');
  const alerts=await(await fetch('/api/alerts')).json();
  if(!alerts.length){container.innerHTML='<div class="loading-state" style="padding:60px;text-align:center"><div style="font-size:48px;margin-bottom:12px">✅</div><div style="color:var(--text-muted)">No active alerts at this time</div></div>';return;}
  container.innerHTML=alerts.map(a=>`
    <div class="alert-card alert-${a.alert_type.toLowerCase()}">
      <div class="alert-icon">${a.alert_type==='AMBER'?'🟡':a.alert_type==='SILVER'?'⚪':'🔴'}</div>
      <div class="alert-body">
        <div class="alert-title"><h4>${a.case_name||'Unknown'}</h4><span class="alert-type-badge alert-badge-${a.alert_type.toLowerCase()}">${a.alert_type}</span></div>
        <div class="alert-message">${a.message}</div>
        <div class="alert-footer">
          <span>📋 ${a.case_number}</span><span>👤 Issued by: ${a.created_by}</span><span>🕐 ${a.created_at}</span>
          ${USER_ROLE!=='PUBLIC'?`<button class="action-btn" style="margin-left:auto" onclick="dismissAlert(${a.id},this)">Dismiss</button>`:''}
        </div>
      </div>
    </div>`).join('');
}
async function dismissAlert(id,btn) {
  if(!confirm('Dismiss this alert?')) return;
  btn.textContent='Dismissing…'; btn.disabled=true;
  const d=await(await fetch(`/api/alerts/${id}/dismiss`,{method:'POST'})).json();
  if(d.success){showToast('Alert dismissed','success');renderAlerts();}else showToast('Failed','error');
}
document.getElementById('create-alert-btn')?.addEventListener('click',async()=>{
  const cases=await(await fetch('/api/cases?status=Missing')).json();
  const sel=document.getElementById('alert-case-id');
  sel.innerHTML=cases.length?cases.map(c=>`<option value="${c.id}">${c.case_number} — ${c.name}</option>`).join(''):'<option value="">No missing cases</option>';
  document.getElementById('alert-form-modal').classList.remove('hidden');
});
document.querySelectorAll('.alert-type-btn').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelectorAll('.alert-type-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); selAlertType=btn.dataset.type;
}));
document.getElementById('cancel-alert')?.addEventListener('click',()=>document.getElementById('alert-form-modal').classList.add('hidden'));
document.getElementById('close-alert-form')?.addEventListener('click',()=>document.getElementById('alert-form-modal').classList.add('hidden'));
document.getElementById('submit-alert')?.addEventListener('click',async()=>{
  const caseId=document.getElementById('alert-case-id').value;
  const message=document.getElementById('alert-message').value.trim();
  if(!message){showToast('Please enter alert message','error');return;}
  const d=await(await fetch('/api/alerts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_id:caseId,alert_type:selAlertType,message})})).json();
  if(d.success){document.getElementById('alert-form-modal').classList.add('hidden');showToast('🚨 Alert issued!','success');renderAlerts();}
});
renderAlerts();
