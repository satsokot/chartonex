function showToast(msg, ok) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast ' + (ok ? 'toast-ok' : 'toast-err');
  setTimeout(function() { t.classList.add('hidden'); }, 3500);
}

function copyCronUrl() {
  var el = document.getElementById('cron-url-text');
  if (!el) return;
  navigator.clipboard.writeText(el.textContent.trim()).then(function() {
    showToast('آدرس کپی شد', true);
  });
}

function testBot() {
  var fd = new FormData();
  fd.append('action', 'test_bot');
  fetch(location.href, { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) showToast('ربات @' + d.username + ' متصل شد ✓', true);
      else showToast('خطا: ' + (d.error || 'نامشخص'), false);
    })
    .catch(function() { showToast('خطای شبکه', false); });
}

function runNow() {
  showToast('در حال اجرا...', true);
  var fd = new FormData();
  fd.append('action', 'run_now');
  fetch(location.href, { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var el = document.getElementById('run-output');
      if (el) {
        el.textContent = d.output || '(بدون خروجی)';
        el.classList.remove('hidden');
      }
      showToast(d.ok ? 'اجرا شد' : 'خطا', d.ok);
    })
    .catch(function() { showToast('خطای شبکه', false); });
}

// Live preview
function updatePreview() {
  var b1 = document.getElementById('inp-btn1');
  var b2 = document.getElementById('inp-btn2');
  var thr = document.getElementById('inp-threshold');
  var ded = document.getElementById('inp-deduction');
  if (b1) { var e = document.getElementById('preview-btn1'); if (e) e.textContent = b1.value || 'دکمه ۱'; }
  if (b2) { var e = document.getElementById('preview-btn2'); if (e) e.textContent = b2.value || 'دکمه ۲'; }
  if (thr) { var e = document.getElementById('f-threshold'); if (e) e.textContent = thr.value; }
  if (ded) { var e = document.getElementById('f-deduction'); if (e) e.textContent = ded.value; }
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('input, textarea').forEach(function(el) {
    el.addEventListener('input', updatePreview);
  });
});
