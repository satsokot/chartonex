<?php
require_once __DIR__ . '/config.php';

// ===== DB =====
function db(): PDO {
    static $pdo = null;
    if (!$pdo) {
        $pdo = new PDO(
            "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET,
            DB_USER, DB_PASS,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]
        );
    }
    return $pdo;
}
function cfg(string $k, string $d = ''): string {
    $r = db()->prepare("SELECT `value` FROM settings WHERE `key`=?");
    $r->execute([$k]);
    $row = $r->fetch();
    return $row ? (string)$row['value'] : $d;
}
function cfg_set(string $k, string $v): void {
    db()->prepare("INSERT INTO settings (`key`,`value`) VALUES (?,?) ON DUPLICATE KEY UPDATE `value`=?")->execute([$k,$v,$v]);
}

// ===== SESSION =====
session_name('chartonex');
session_start();

// ===== ACTIONS =====
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $a = $_POST['action'] ?? '';

    if ($a === 'login') {
        if (($_POST['u'] ?? '') === ADMIN_USER && ($_POST['p'] ?? '') === ADMIN_PASS) {
            $_SESSION['ok'] = true;
            header('Location: index.php'); exit;
        }
        $err = 'نام کاربری یا رمز اشتباه است';
    }

    if ($a === 'logout') { session_destroy(); header('Location: index.php'); exit; }

    if ($a === 'save' && !empty($_SESSION['ok'])) {
        foreach (['source_channel','dest_channel','difference_threshold','price_deduction',
                  'bot_token','button1_text','button1_url','button2_text','button2_url','message_template'] as $f) {
            if (isset($_POST[$f])) cfg_set($f, trim($_POST[$f]));
        }
        $ok = 'تنظیمات ذخیره شد';
    }

    if ($a === 'test_bot' && !empty($_SESSION['ok'])) {
        $token = cfg('bot_token');
        $ch = curl_init("https://api.telegram.org/bot{$token}/getMe");
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>1, CURLOPT_TIMEOUT=>10]);
        $res = json_decode(curl_exec($ch), true); curl_close($ch);
        header('Content-Type: application/json');
        echo json_encode($res['ok'] ? ['ok'=>true,'u'=>$res['result']['username']] : ['ok'=>false,'e'=>$res['description']??'خطا']);
        exit;
    }

    if ($a === 'run_now' && !empty($_SESSION['ok'])) {
        $cron_token = cfg('cron_token');
        $proto = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $base  = rtrim(dirname($_SERVER['PHP_SELF']), '/');
        $cron_url_now = $proto . '://' . $_SERVER['HTTP_HOST'] . $base . '/cron.php?token=' . urlencode($cron_token);
        $ch = curl_init($cron_url_now);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>1, CURLOPT_TIMEOUT=>30, CURLOPT_FOLLOWLOCATION=>1,
            CURLOPT_USERAGENT=>'Chartonex-Admin/1.0']);
        $out = curl_exec($ch);
        $err = curl_error($ch);
        curl_close($ch);
        header('Content-Type: application/json');
        echo json_encode(['ok'=>true,'out'=>($out ?: ('curl error: '.$err))]); exit;
    }
}

// ===== LOGIN PAGE =====
if (empty($_SESSION['ok'])) { ?>
<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ورود - Chartonex</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Tahoma,Arial,sans-serif;background:#0f1117;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#161b27;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:48px 40px;width:100%;max-width:400px}
h1{text-align:center;font-size:22px;margin:16px 0 4px}.sub{text-align:center;color:#64748b;font-size:13px;margin-bottom:32px}
label{display:block;font-size:13px;color:#94a3b8;margin-bottom:6px}
input{width:100%;background:#1e2535;border:1px solid rgba(255,255,255,.08);border-radius:8px;color:#e2e8f0;padding:10px 14px;font-size:14px;font-family:inherit;outline:none;margin-bottom:16px}
input:focus{border-color:#3b82f6}
.btn{width:100%;background:#3b82f6;color:#fff;border:none;border-radius:8px;padding:12px;font-size:15px;font-family:inherit;cursor:pointer;margin-top:4px}
.btn:hover{background:#2563eb}
.err{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#ef4444;padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:16px}
.logo{font-size:48px;text-align:center}
</style></head><body>
<div class="card">
  <div class="logo">💵</div>
  <h1>Chartonex Bot</h1>
  <p class="sub">پنل مدیریت قیمت تتر</p>
  <?php if(!empty($err)) echo "<div class='err'>$err</div>"; ?>
  <form method="post">
    <input type="hidden" name="action" value="login">
    <label>نام کاربری</label><input type="text" name="u" autofocus>
    <label>رمز عبور</label><input type="password" name="p">
    <button class="btn">ورود به پنل</button>
  </form>
</div>
</body></html>
<?php exit; }

// ===== DASHBOARD =====
$S = [];
$rows = db()->query("SELECT `key`,`value` FROM settings")->fetchAll();
foreach ($rows as $r) $S[$r['key']] = $r['value'];
$logs = db()->query("SELECT * FROM price_logs ORDER BY id DESC LIMIT 30")->fetchAll();
$cron_url = (isset($_SERVER['HTTPS'])?'https':'http').'://'.$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']).'/cron.php?token='.urlencode($S['cron_token']??'');
?>
<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chartonex - پنل ادمین</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0f1117;--bg2:#161b27;--bg3:#1e2535;--brd:rgba(255,255,255,.08);--acc:#3b82f6;--grn:#22c55e;--red:#ef4444;--tx:#e2e8f0;--tx2:#94a3b8;--tx3:#64748b}
body{font-family:Tahoma,Arial,sans-serif;background:var(--bg);color:var(--tx);display:flex;min-height:100vh}
/* sidebar */
.sb{width:210px;background:var(--bg2);border-left:1px solid var(--brd);display:flex;flex-direction:column;position:fixed;right:0;top:0;bottom:0}
.sb-top{padding:20px;border-bottom:1px solid var(--brd);font-size:18px;font-weight:700;color:var(--acc)}
.sb nav a{display:block;padding:10px 20px;color:var(--tx2);text-decoration:none;font-size:14px;border-right:3px solid transparent}
.sb nav a:hover{color:var(--tx);background:rgba(59,130,246,.08);border-right-color:var(--acc)}
.sb-bot{padding:16px 20px;border-top:1px solid var(--brd);margin-top:auto}
/* main */
.main{margin-right:210px;flex:1;padding:28px 32px;max-width:880px}
/* card */
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;margin-bottom:24px;overflow:hidden}
.ch{padding:16px 24px;border-bottom:1px solid var(--brd);font-size:15px;font-weight:600;display:flex;align-items:center;justify-content:space-between}
.cb{padding:24px}
/* form */
.fg{margin-bottom:16px;flex:1}
.fg label{display:block;font-size:13px;color:var(--tx2);margin-bottom:6px}
.fr{display:flex;gap:16px}
input[type=text],input[type=number],input[type=url],input[type=password],textarea{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:8px;color:var(--tx);padding:10px 14px;font-size:14px;font-family:inherit;outline:none}
input:focus,textarea:focus{border-color:var(--acc)}
textarea{resize:vertical;min-height:90px}
.iu{display:flex;align-items:center;gap:8px}.iu input{flex:1}.unit{color:var(--tx3);font-size:13px}
/* buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;font-family:inherit;cursor:pointer;border:none;text-decoration:none;gap:6px}
.btn-p{background:var(--acc);color:#fff}.btn-p:hover{background:#2563eb}
.btn-g{background:var(--grn);color:#fff}.btn-g:hover{background:#16a34a}
.btn-o{background:transparent;border:1px solid var(--brd);color:var(--tx2)}.btn-o:hover{border-color:var(--acc);color:var(--acc)}
.btn-sm{padding:6px 12px;font-size:12px}.btn-full{width:100%}
.btn-lg{padding:14px 32px;font-size:16px}
.bg{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
/* cron */
.cbox{display:flex;align-items:center;gap:12px;background:var(--bg3);border:1px solid rgba(59,130,246,.3);border-radius:8px;padding:12px 16px;margin-bottom:20px;overflow:hidden}
.cbox code{font-size:12px;color:#93c5fd;flex:1;word-break:break-all;direction:ltr;text-align:left}
.steps{background:var(--bg3);border-radius:8px;padding:16px 20px}
.steps p{font-weight:600;font-size:14px;margin-bottom:10px}
.steps ol{padding-right:20px}
.steps li{font-size:13px;color:var(--tx2);margin-bottom:6px;line-height:1.8}
.steps code{background:rgba(255,255,255,.08);padding:2px 6px;border-radius:4px;font-size:12px;direction:ltr;display:inline-block}
/* formula */
.fbox{background:var(--bg3);border:1px solid rgba(59,130,246,.2);border-radius:8px;padding:16px 20px;margin-top:16px}
.formula{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:14px;margin-bottom:8px}
.op{color:var(--acc);font-weight:700;font-size:16px}
.val{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.2);border-radius:6px;padding:2px 10px;color:var(--acc)}
.fnote{font-size:12px;color:var(--tx3)}
/* tg preview */
.tgp{margin-top:20px;background:#212d3b;border-radius:12px;overflow:hidden;max-width:360px}
.tgph{background:#1a2535;padding:8px 16px;font-size:12px;color:var(--tx3)}
.tgm{padding:12px 12px 8px}
.tgt{background:#182533;border-radius:12px 12px 12px 0;padding:12px 14px;font-size:14px;line-height:1.7;color:#e1e8ed;margin-bottom:8px}
.tgbs{display:flex;gap:6px}
.tgb{flex:1;text-align:center;padding:8px 10px;border-radius:8px;font-size:13px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:#7ab8e8}
/* table */
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{padding:10px 12px;text-align:right;color:var(--tx3);font-weight:500;border-bottom:1px solid var(--brd);white-space:nowrap}
td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.04);white-space:nowrap}
tr:hover td{background:rgba(255,255,255,.02)}
.ab{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-family:monospace}
.a-sent{background:rgba(34,197,94,.15);color:var(--grn)}
.a-no_action{background:rgba(100,116,139,.15);color:var(--tx3)}
.a-err{background:rgba(239,68,68,.15);color:var(--red)}
/* misc */
.alert-s{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:var(--grn);padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:14px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);padding:12px 24px;border-radius:8px;font-size:14px;z-index:9999;display:none}
.tok{background:var(--bg3);border:1px solid rgba(34,197,94,.4);color:var(--grn)}
.ter{background:var(--bg3);border:1px solid rgba(239,68,68,.4);color:var(--red)}
.tx2{color:var(--tx2)}.tx3{color:var(--tx3)}.txg{color:var(--grn)}.txr{color:var(--red)}.tc{text-align:center}
.ro{background:#0a0f1a;border:1px solid var(--brd);border-radius:8px;padding:12px 16px;font-family:monospace;font-size:13px;color:var(--grn);direction:ltr;white-space:pre-wrap;margin-top:12px;display:none}
.hint{font-size:11px;color:var(--tx3);font-weight:400}
@media(max-width:768px){.sb{display:none}.main{margin-right:0;padding:16px}.fr{flex-direction:column}}
</style></head><body>

<aside class="sb">
  <div class="sb-top">💵 Chartonex</div>
  <nav>
    <a href="#cron">⏱ Cron Job</a>
    <a href="#channels">📡 کانال‌ها</a>
    <a href="#thresh">📊 آستانه‌ها</a>
    <a href="#msg">💬 پیام و دکمه‌ها</a>
    <a href="#bot">🤖 ربات</a>
    <a href="#logs">📋 لاگ‌ها</a>
  </nav>
  <div class="sb-bot">
    <form method="post"><input type="hidden" name="action" value="logout">
    <button class="btn btn-o btn-sm btn-full">خروج</button></form>
  </div>
</aside>

<main class="main">
<div id="toast" class="toast"></div>
<?php if(!empty($ok)) echo "<div class='alert-s'>$ok</div>"; ?>

<!-- CRON -->
<div class="card" id="cron">
  <div class="ch"><span>⏱ تنظیم Cron Job</span></div>
  <div class="cb">
    <p style="font-size:13px;color:var(--tx2);margin-bottom:12px">آدرس زیر را در Cron Job هاست وارد کنید:</p>
    <div class="cbox">
      <code id="curl"><?=htmlspecialchars($cron_url)?></code>
      <button class="btn btn-o btn-sm" onclick="cp()">کپی</button>
    </div>
    <div class="steps">
      <p>مراحل در DirectAdmin:</p>
      <ol>
        <li>برو به <strong>Advanced Features → Cronjobs</strong></li>
        <li>روی <strong>Add Cronjob</strong> کلیک کن</li>
        <li>در بخش <strong>Command</strong> یکی از دستورات زیر را وارد کن:<br><br>
          <strong>گزینه ۱ (wget):</strong><br>
          <div class="cbox" style="margin:6px 0 10px"><code id="cmd1">/usr/bin/wget -q -O /dev/null "<?=htmlspecialchars($cron_url)?>"</code><button class="btn btn-o btn-sm" onclick="copyText('cmd1')">کپی</button></div>
          <strong>گزینه ۲ (curl):</strong><br>
          <div class="cbox" style="margin:6px 0"><code id="cmd2">/usr/local/bin/curl --silent -L "<?=htmlspecialchars($cron_url)?>"</code><button class="btn btn-o btn-sm" onclick="copyText('cmd2')">کپی</button></div>
        </li>
        <li>در بخش زمان‌بندی وارد کن: <code>*/5 * * * *</code> (هر ۵ دقیقه)<br>
          <span style="font-size:12px;color:var(--tx3)">یا فیلدهای جداگانه: Minute=<strong>*/5</strong> و بقیه = <strong>*</strong></span></li>
        <li>ذخیره کن</li>
      </ol>
    </div>
    <div class="bg">
      <button class="btn btn-g" onclick="runNow()">▶ تست فوری</button>
    </div>
    <div class="ro" id="ro"></div>
  </div>
</div>

<form method="post">
<input type="hidden" name="action" value="save">

<!-- CHANNELS -->
<div class="card" id="channels">
  <div class="ch">📡 کانال‌ها</div>
  <div class="cb">
    <div class="fr">
      <div class="fg"><label>کانال مبدا <span class="hint">(کانال عمومی)</span></label>
        <input type="text" name="source_channel" value="<?=htmlspecialchars($S['source_channel']??'')?>" placeholder="@source_channel" dir="ltr"></div>
      <div class="fg"><label>کانال مقصد <span class="hint">(ربات باید ادمین آن باشد)</span></label>
        <input type="text" name="dest_channel" value="<?=htmlspecialchars($S['dest_channel']??'')?>" placeholder="@dest_channel" dir="ltr"></div>
    </div>
  </div>
</div>

<!-- THRESHOLDS -->
<div class="card" id="thresh">
  <div class="ch">📊 آستانه‌های قیمتی</div>
  <div class="cb">
    <div class="fr">
      <div class="fg"><label>آستانه اختلاف <span class="hint">(اگر اختلاف بیشتر بود ارسال می‌شود)</span></label>
        <div class="iu"><input type="number" name="difference_threshold" id="it" value="<?=htmlspecialchars($S['difference_threshold']??'300')?>" min="0" step="10"><span class="unit">تومان</span></div></div>
      <div class="fg"><label>مقدار کسر <span class="hint">(از میانگین کم می‌شود)</span></label>
        <div class="iu"><input type="number" name="price_deduction" id="id" value="<?=htmlspecialchars($S['price_deduction']??'100')?>" min="0" step="10"><span class="unit">تومان</span></div></div>
    </div>
    <div class="fbox">
      <div class="formula">
        <span>قیمت ارسالی</span><span class="op">=</span>
        <span class="val">میانگین (خرید+فروش)÷۲</span><span class="op">−</span>
        <span class="val" id="fd"><?=htmlspecialchars($S['price_deduction']??'100')?></span><span class="unit">تومان</span>
      </div>
      <p class="fnote">فقط وقتی اختلاف بیشتر از <strong id="ft"><?=htmlspecialchars($S['difference_threshold']??'300')?></strong> تومان باشد</p>
    </div>
  </div>
</div>

<!-- MESSAGE -->
<div class="card" id="msg">
  <div class="ch">💬 قالب پیام و دکمه‌ها</div>
  <div class="cb">
    <div class="fg"><label>قالب پیام <span class="hint">({price}=قیمت، {date}=تاریخ شمسی)</span></label>
      <textarea name="message_template"><?=htmlspecialchars($S['message_template']??'')?></textarea></div>
    <div class="fr">
      <div class="fg"><label>متن دکمه ۱</label><input type="text" name="button1_text" id="b1" value="<?=htmlspecialchars($S['button1_text']??'دانلود اپلیکیشن')?>"></div>
      <div class="fg"><label>لینک دکمه ۱</label><input type="url" name="button1_url" value="<?=htmlspecialchars($S['button1_url']??'')?>" placeholder="https://..." dir="ltr"></div>
    </div>
    <div class="fr">
      <div class="fg"><label>متن دکمه ۲</label><input type="text" name="button2_text" id="b2" value="<?=htmlspecialchars($S['button2_text']??'پشتیبانی')?>"></div>
      <div class="fg"><label>لینک دکمه ۲</label><input type="url" name="button2_url" value="<?=htmlspecialchars($S['button2_url']??'')?>" placeholder="https://t.me/..." dir="ltr"></div>
    </div>
    <div class="tgp">
      <div class="tgph">پیش‌نمایش پیام تلگرام</div>
      <div class="tgm">
        <div class="tgt">قیمت تتر : <strong>167,500</strong> تومان 💵 USDT<br>─────────────────<br>تاریخ: <?=date('Y/m/d')?></div>
        <div class="tgbs">
          <span class="tgb" id="pb1"><?=htmlspecialchars($S['button1_text']??'دانلود اپلیکیشن')?></span>
          <span class="tgb" id="pb2"><?=htmlspecialchars($S['button2_text']??'پشتیبانی')?></span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- BOT -->
<div class="card" id="bot">
  <div class="ch">🤖 توکن ربات تلگرام</div>
  <div class="cb">
    <p style="font-size:13px;color:var(--tx2);margin-bottom:16px">از <strong>@BotFather</strong> ربات بسازید، توکن را بگیرید و ربات را ادمین کانال مقصد کنید.</p>
    <div class="fg"><label>Bot Token</label>
      <input type="text" name="bot_token" value="<?=htmlspecialchars($S['bot_token']??'')?>" placeholder="1234567890:ABCdef..." dir="ltr"></div>
    <button type="button" class="btn btn-o" onclick="testBot()">تست توکن</button>
  </div>
</div>

<div style="margin-bottom:24px">
  <button type="submit" class="btn btn-p btn-lg">💾 ذخیره همه تنظیمات</button>
</div>
</form>

<!-- LOGS -->
<div class="card" id="logs">
  <div class="ch"><span>📋 لاگ‌های اخیر</span>
    <a href="index.php#logs" class="btn btn-o btn-sm">↻</a></div>
  <div class="cb">
    <div class="tw"><table>
      <thead><tr><th>زمان</th><th>خرید</th><th>فروش</th><th>میانگین</th><th>مقصد</th><th>اختلاف</th><th>ارسالی</th><th>نتیجه</th></tr></thead>
      <tbody>
      <?php if(empty($logs)): ?>
        <tr><td colspan="8" class="tc tx3">هنوز لاگی ثبت نشده</td></tr>
      <?php else: foreach($logs as $l): ?>
        <tr>
          <td><?=substr($l['created_at']??'',5,11)?></td>
          <td><?=$l['source_buy']?number_format($l['source_buy']):'—'?></td>
          <td><?=$l['source_sell']?number_format($l['source_sell']):'—'?></td>
          <td><?=$l['source_avg']?number_format($l['source_avg']):'—'?></td>
          <td><?=$l['dest_price']?number_format($l['dest_price']):'—'?></td>
          <td class="<?=($l['difference']??0)>($S['difference_threshold']??300)?'txr':''?>"><?=$l['difference']?number_format($l['difference']):'—'?></td>
          <td class="txg"><?=$l['sent_price']?number_format($l['sent_price']):'—'?></td>
          <td><span class="ab <?=str_contains($l['action']??'','error')||str_contains($l['action']??'','missing')?'a-err':($l['action']=='sent'?'a-sent':'a-no_action')?>"><?=htmlspecialchars($l['action']??'')?></span></td>
        </tr>
      <?php endforeach; endif; ?>
      </tbody>
    </table></div>
  </div>
</div>
</main>

<script>
function toast(m,ok){var t=document.getElementById('toast');t.textContent=m;t.className='toast '+(ok?'tok':'ter');t.style.display='block';setTimeout(function(){t.style.display='none'},3000)}
function cp(){navigator.clipboard.writeText(document.getElementById('curl').textContent.trim()).then(function(){toast('کپی شد',true)})}
function copyText(id){navigator.clipboard.writeText(document.getElementById(id).textContent.trim()).then(function(){toast('کپی شد',true)})}
function testBot(){
  var fd=new FormData();fd.append('action','test_bot');
  fetch('index.php',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
    toast(d.ok?'ربات @'+d.u+' متصل شد ✓':'خطا: '+(d.e||'نامشخص'),d.ok)
  })
}
function runNow(){
  toast('در حال اجرا...',true);
  var fd=new FormData();fd.append('action','run_now');
  fetch('index.php',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
    var el=document.getElementById('ro');el.textContent=d.out||'(بدون خروجی)';el.style.display='block';
    toast(d.ok?'اجرا شد':'خطا',d.ok)
  })
}
function upd(){
  var b1=document.getElementById('b1'),b2=document.getElementById('b2'),it=document.getElementById('it'),id=document.getElementById('id');
  if(b1){var e=document.getElementById('pb1');if(e)e.textContent=b1.value||'دکمه ۱'}
  if(b2){var e=document.getElementById('pb2');if(e)e.textContent=b2.value||'دکمه ۲'}
  if(it){var e=document.getElementById('ft');if(e)e.textContent=it.value}
  if(id){var e=document.getElementById('fd');if(e)e.textContent=id.value}
}
document.querySelectorAll('input,textarea').forEach(function(e){e.addEventListener('input',upd)})
</script>
</body></html>
