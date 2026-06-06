const roleButtons = document.querySelectorAll('.role-btn');
let selectedRole = 'PUBLIC';
roleButtons.forEach(btn => btn.addEventListener('click', () => {
  roleButtons.forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  selectedRole = btn.dataset.role;
}));
document.getElementById('toggle-pw').addEventListener('click', () => {
  const pw = document.getElementById('password');
  pw.type = pw.type === 'password' ? 'text' : 'password';
});
document.querySelectorAll('.cred-chip').forEach(chip => chip.addEventListener('click', () => {
  document.getElementById('username').value = chip.dataset.u;
  document.getElementById('password').value = chip.dataset.p;
  roleButtons.forEach(b => b.classList.toggle('active', b.dataset.role === chip.dataset.r));
  selectedRole = chip.dataset.r;
}));
async function doLogin() {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  if (!username || !password) { showAlert('Please enter username and password.'); return; }
  const btn = document.getElementById('login-btn');
  btn.querySelector('.btn-text').classList.add('hidden');
  btn.querySelector('.btn-spinner').classList.remove('hidden');
  btn.disabled = true;
  try {
    const res = await fetch('/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password,role:selectedRole})});
    const d = await res.json();
    if (d.success) { window.location.href = d.redirect; return; }
    showAlert(d.message || 'Login failed');
    // Show attempt warning bar
    const match = (d.message||'').match(/(\d+) attempt/);
    if (match) {
      const left = parseInt(match[1]);
      document.getElementById('attempts-bar').classList.remove('hidden');
      document.getElementById('attempts-text').textContent = `⚠️ ${left} attempt(s) remaining before lockout`;
      document.getElementById('attempts-fill').style.width = ((5-left)/5*100)+'%';
    }
  } catch { showAlert('Network error. Please try again.'); }
  finally { btn.querySelector('.btn-text').classList.remove('hidden'); btn.querySelector('.btn-spinner').classList.add('hidden'); btn.disabled = false; }
}
function showAlert(msg) { const b=document.getElementById('alert-box'); b.textContent=msg; b.className='alert error'; }
document.getElementById('login-btn').addEventListener('click', doLogin);
document.getElementById('password').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });
document.getElementById('username').addEventListener('keydown', e => { if(e.key==='Enter') document.getElementById('password').focus(); });
