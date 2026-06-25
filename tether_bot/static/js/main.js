// ===== Toast =====
function showToast(message, ok = true) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = message;
  t.className = 'toast ' + (ok ? 'toast-ok' : 'toast-err');
  setTimeout(() => t.classList.add('hidden'), 3500);
}

// ===== Bot Controls =====
async function botStart() {
  const res = await fetch('/bot/start', { method: 'POST' });
  const data = await res.json();
  showToast(data.message, data.ok);
  if (data.ok) {
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-stop').disabled = false;
    document.getElementById('status-badge').innerHTML = '<span class="badge badge-green">فعال</span>';
  }
}

async function botStop() {
  const res = await fetch('/bot/stop', { method: 'POST' });
  const data = await res.json();
  showToast(data.message, data.ok);
  if (data.ok) {
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').disabled = true;
    document.getElementById('status-badge').innerHTML = '<span class="badge badge-red">متوقف</span>';
    document.getElementById('next-run').textContent = '—';
  }
}

async function botRunNow() {
  showToast('در حال بررسی قیمت...', true);
  const res = await fetch('/bot/run-now', { method: 'POST' });
  const data = await res.json();
  showToast(data.message, data.ok);
  if (data.ok) loadStatus();
}

// ===== Status Polling =====
async function loadStatus() {
  try {
    const res = await fetch('/bot/status');
    const data = await res.json();

    const nextEl = document.getElementById('next-run');
    if (nextEl) nextEl.textContent = data.next_run || '—';

    if (data.last_log) {
      const l = data.last_log;
      setEl('last-avg', l.source_avg ? num(l.source_avg) : '—');
      setEl('last-dest', l.dest_price ? num(l.dest_price) : '—');
      setEl('last-diff', l.difference ? num(l.difference) : '—');
      setEl('last-sent', l.sent_price ? num(l.sent_price) : '—');
      setEl('last-action', l.action_taken || '—');
    }
  } catch (e) { /* ignore */ }
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function num(n) {
  return Number(n).toLocaleString('fa-IR');
}

// Poll status every 30s
loadStatus();
setInterval(loadStatus, 30000);

// ===== Telegram Auth =====
async function saveAndConnect() {
  // Save form first
  const form = document.getElementById('settings-form');
  const fd = new FormData(form);
  await fetch('/settings', { method: 'POST', body: fd });

  const res = await fetch('/telegram/connect', { method: 'POST' });
  const data = await res.json();
  if (data.ok) {
    if (data.status === 'already_authorized') {
      showToast('قبلاً متصل شده‌اید', true);
    } else if (data.status === 'code_sent') {
      document.getElementById('otp-section').classList.remove('hidden');
      showToast('کد تأیید ارسال شد', true);
    }
  } else {
    showToast(data.message || 'خطا در اتصال', false);
  }
}

async function verifyOtp() {
  const code = document.getElementById('otp-code').value.trim();
  const password = document.getElementById('otp-password')?.value.trim() || '';
  if (!code) { showToast('کد را وارد کنید', false); return; }

  const fd = new FormData();
  fd.append('code', code);
  if (password) fd.append('password', password);

  const res = await fetch('/telegram/verify', { method: 'POST', body: fd });
  const data = await res.json();
  if (data.ok) {
    showToast(data.message, true);
    document.getElementById('otp-section').classList.add('hidden');
  } else if (data.need_password) {
    document.getElementById('password-group').style.display = 'block';
    showToast('رمز دو مرحله‌ای را وارد کنید', false);
  } else {
    showToast(data.message || 'خطا', false);
  }
}

async function testBot() {
  const res = await fetch('/telegram/test-bot', { method: 'POST' });
  const data = await res.json();
  showToast(data.message || (data.ok ? 'موفق' : 'خطا'), data.ok);
}

// ===== Live Preview =====
function updatePreview() {
  const b1 = document.querySelector('[name="button1_text"]');
  const b2 = document.querySelector('[name="button2_text"]');
  const threshold = document.querySelector('[name="difference_threshold"]');
  const deduction = document.querySelector('[name="price_deduction"]');

  if (b1) {
    const el = document.getElementById('preview-btn1');
    if (el) el.textContent = b1.value || 'دکمه ۱';
  }
  if (b2) {
    const el = document.getElementById('preview-btn2');
    if (el) el.textContent = b2.value || 'دکمه ۲';
  }
  if (threshold) {
    const el = document.getElementById('formula-threshold');
    if (el) el.textContent = threshold.value;
  }
  if (deduction) {
    const el = document.getElementById('formula-deduction');
    if (el) el.textContent = deduction.value;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input, textarea').forEach(el => {
    el.addEventListener('input', updatePreview);
  });
});

// ===== Load Logs =====
async function loadLogs() {
  try {
    const res = await fetch('/logs');
    const data = await res.json();
    const tbody = document.getElementById('log-tbody');
    if (!tbody) return;

    if (!data.logs.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">لاگی موجود نیست</td></tr>';
      return;
    }

    tbody.innerHTML = data.logs.map(l => `
      <tr>
        <td>${l.created_at || '—'}</td>
        <td>${l.source_buy ? Number(l.source_buy).toLocaleString() : '—'}</td>
        <td>${l.source_sell ? Number(l.source_sell).toLocaleString() : '—'}</td>
        <td>${l.source_avg ? Number(l.source_avg).toLocaleString() : '—'}</td>
        <td>${l.dest_price ? Number(l.dest_price).toLocaleString() : '—'}</td>
        <td class="${l.difference > 300 ? 'text-red' : ''}">${l.difference ? Number(l.difference).toLocaleString() : '—'}</td>
        <td class="text-green">${l.sent_price ? Number(l.sent_price).toLocaleString() : '—'}</td>
        <td><span class="action-badge action-${l.action_taken}">${l.action_taken}</span></td>
      </tr>
    `).join('');
  } catch (e) { /* ignore */ }
}
