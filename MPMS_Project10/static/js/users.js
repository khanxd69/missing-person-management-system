let allUsers=[], editUserId=null;
async function loadUsers(){allUsers=await(await fetch('/api/users')).json();renderUsers();}
function renderUsers(){
  const s=document.getElementById('user-search').value.toLowerCase(), r=document.getElementById('role-filter').value;
  const f=allUsers.filter(u=>(!s||(u.username+' '+(u.full_name||'')).toLowerCase().includes(s))&&(!r||u.role===r));
  const tbody=document.getElementById('users-tbody');
  if(!f.length){tbody.innerHTML='<tr><td colspan="7" class="loading-cell">No users found</td></tr>';return;}
  tbody.innerHTML=f.map(u=>`<tr>
    <td><div style="display:flex;align-items:center;gap:10px"><div style="width:32px;height:32px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:white">${(u.full_name||u.username)[0].toUpperCase()}</div><div><div style="font-size:13px;font-weight:600">${u.full_name||'—'}</div><div style="font-size:11px;color:var(--text-muted)">${u.email||'—'}</div></div></div></td>
    <td><code style="font-size:12px;color:var(--blue-light)">${u.username}</code></td>
    <td><span class="role-badge role-${u.role.toLowerCase()}">${u.role.replace('_',' ')}</span></td>
    <td style="font-size:12px;color:var(--text-muted)">${u.badge_number||'—'}</td>
    <td>${u.is_locked?'<span class="status-badge status-missing">Locked</span>':u.is_active?'<span class="status-badge status-located">Active</span>':'<span class="status-badge status-closed">Inactive</span>'}</td>
    <td style="font-size:12px;color:var(--text-muted)">${u.last_login}</td>
    <td><div class="table-actions"><button class="action-btn" onclick='openUserForm(${JSON.stringify(u)})'>Edit</button><button class="action-btn danger" onclick="deleteUser(${u.id})">Delete</button></div></td>
  </tr>`).join('');
}
function openUserForm(data=null){
  editUserId=data?.id||null;
  document.getElementById('user-form-title').textContent=data?'Edit User':'Add New User';
  document.getElementById('submit-user-btn').textContent=data?'Save Changes':'Add User';
  document.getElementById('pw-label').textContent=data?'New Password (leave blank to keep)':'Password *';
  document.getElementById('active-field').style.display=data?'':'none';
  document.getElementById('unlock-field').style.display=(data&&data.is_locked)?'':'none';
  document.getElementById('u-fullname').value=data?.full_name||'';
  document.getElementById('u-username').value=data?.username||'';
  document.getElementById('u-role').value=data?.role||'PUBLIC';
  document.getElementById('u-badge').value=data?.badge_number||'';
  document.getElementById('u-email').value=data?.email||'';
  document.getElementById('u-phone').value=data?.phone||'';
  document.getElementById('u-password').value='';
  if(data){document.getElementById('u-active').checked=data.is_active;document.getElementById('u-unlock').checked=false;}
  document.getElementById('user-form-modal').classList.remove('hidden');
}
document.getElementById('add-user-btn').addEventListener('click',()=>openUserForm());
document.getElementById('close-user-form').addEventListener('click',()=>document.getElementById('user-form-modal').classList.add('hidden'));
document.getElementById('cancel-user-form').addEventListener('click',()=>document.getElementById('user-form-modal').classList.add('hidden'));
document.getElementById('submit-user-btn').addEventListener('click',async()=>{
  const body={full_name:document.getElementById('u-fullname').value,username:document.getElementById('u-username').value,role:document.getElementById('u-role').value,badge_number:document.getElementById('u-badge').value,email:document.getElementById('u-email').value,phone:document.getElementById('u-phone').value,password:document.getElementById('u-password').value,is_active:document.getElementById('u-active')?.checked??true,unlock:document.getElementById('u-unlock')?.checked??false};
  if(!body.username){showToast('Username required','error');return;}
  if(!editUserId&&!body.password){showToast('Password required','error');return;}
  const url=editUserId?`/api/users/${editUserId}`:'/api/users',method=editUserId?'PUT':'POST';
  const d=await(await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  if(d.success){document.getElementById('user-form-modal').classList.add('hidden');showToast(editUserId?'✅ User updated':'✅ User added','success');loadUsers();}
  else showToast(d.error||'Failed','error');
});
async function deleteUser(id){
  if(!confirm('Delete this user permanently?')) return;
  const d=await(await fetch(`/api/users/${id}`,{method:'DELETE'})).json();
  if(d.success){showToast('User deleted','success');loadUsers();}else showToast(d.error||'Failed','error');
}
let st;
document.getElementById('user-search').addEventListener('input',()=>{clearTimeout(st);st=setTimeout(renderUsers,200);});
document.getElementById('role-filter').addEventListener('change',renderUsers);
loadUsers();
