<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/auth.php';
require_once __DIR__ . '/includes/telegram.php';

// ----- Handle POST actions -----
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    // Login
    if ($action === 'login') {
        if (try_login($_POST['username'] ?? '', $_POST['password'] ?? '')) {
            header('Location: ' . $_SERVER['PHP_SELF']);
        } else {
            $login_error = 'نام کاربری یا رمز عبور اشتباه است';
        }
    }

    // Logout
    if ($action === 'logout') {
        do_logout();
        header('Location: ' . $_SERVER['PHP_SELF']);
        exit;
    }

    // Save settings
    if ($action === 'save_settings' && is_logged_in()) {
        $fields = [
            'source_channel','dest_channel','difference_threshold','price_deduction',
            'check_interval_minutes','bot_token','button1_text','button1_url',
            'button2_text','button2_url','message_template',
            'admin_username','admin_password',
        ];
        foreach ($fields as $f) {
            if (isset($_POST[$f])) setting_set($f, trim($_POST[$f]));
        }
        $success = 'تنظیمات با موفقیت ذخیره شد';
    }

    // Test bot
    if ($action === 'test_bot' && is_logged_in()) {
        $token  = setting_get('bot_token');
        $result = test_bot($token);
        header('Content-Type: application/json');
        echo json_encode($result);
        exit;
    }

    // Run cron now
    if ($action === 'run_now' && is_logged_in()) {
        ob_start();
        $_GET['token'] = setting_get('cron_token');
        require __DIR__ . '/cron.php';
        $output = ob_get_clean();
        header('Content-Type: application/json');
        echo json_encode(['ok' => true, 'output' => $output]);
        exit;
    }
}

// ----- Show login page -----
if (!is_logged_in()) { ?>
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ورود - Chartonex</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="login-page">
<div class="login-card">
  <div class="login-logo">
    <div class="logo-icon">💵</div>
    <h1>Chartonex Bot</h1>
    <p>پنل مدیریت قیمت تتر</p>
  </div>
  <?php if (!empty($login_error)): ?>
  <div class="alert alert-error"><?= htmlspecialchars($login_error) ?></div>
  <?php endif; ?>
  <form method="post">
    <input type="hidden" name="action" value="login">
    <div class="form-group">
      <label>نام کاربری</label>
      <input type="text" name="username" placeholder="admin" required autofocus>
    </div>
    <div class="form-group">
      <label>رمز عبور</label>
      <input type="password" name="password" placeholder="••••••••" required>
    </div>
    <button type="submit" class="btn btn-primary btn-full">ورود به پنل</button>
  </form>
</div>
</body>
</html>
<?php exit; }

// ----- Dashboard -----
require_once __DIR__ . '/includes/parser.php';

$settings = [];
$db = get_db();
$res = $db->query("SELECT key, value FROM settings");
while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
    $settings[$row['key']] = $row['value'];
}

$logs      = logs_get(30);
$cron_url  = (isset($_SERVER['HTTPS']) ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? 'yoursite.com')
           . dirname($_SERVER['PHP_SELF'] ?? '/') . '/cron.php?token=' . urlencode($settings['cron_token'] ?? '');
?>
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>پنل ادمین - Chartonex</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="dashboard-page">

<aside class="sidebar">
  <div class="sidebar-header">
    <span class="logo-icon">💵</span>
    <span class="logo-text">Chartonex</span>
  </div>
  <nav class="sidebar-nav">
    <a href="#section-cron"       class="nav-item">Cron Job</a>
    <a href="#section-channels"   class="nav-item">کانال‌ها</a>
    <a href="#section-thresholds" class="nav-item">آستانه‌ها</a>
    <a href="#section-message"    class="nav-item">قالب پیام</a>
    <a href="#section-bot"        class="nav-item">ربات تلگرام</a>
    <a href="#section-account"    class="nav-item">حساب کاربری</a>
    <a href="#section-logs"       class="nav-item">لاگ‌ها</a>
  </nav>
  <div class="sidebar-footer">
    <form method="post" style="margin:0">
      <input type="hidden" name="action" value="logout">
      <button type="submit" class="btn btn-outline btn-sm btn-full">خروج</button>
    </form>
  </div>
</aside>

<main class="main-content">

  <?php if (!empty($success)): ?>
  <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
  <?php endif; ?>

  <div id="toast" class="toast hidden"></div>

  <!-- ===== CRON SECTION ===== -->
  <section id="section-cron" class="card">
    <div class="card-header">
      <h2>⏱ تنظیم Cron Job (مهم‌ترین مرحله)</h2>
    </div>
    <div class="card-body">
      <p class="info-text" style="margin-bottom:12px">
        برای اجرای خودکار هر چند دقیقه، باید یک Cron Job در DirectAdmin بسازید.<br>
        آدرس زیر را کپی کرده و در Cron Job هاستتان وارد کنید:
      </p>
      <div class="cron-url-box">
        <code id="cron-url-text"><?= htmlspecialchars($cron_url) ?></code>
        <button class="btn btn-sm btn-outline" onclick="copyCronUrl()">کپی</button>
      </div>
      <div class="cron-steps">
        <p><strong>مراحل ساخت Cron Job در DirectAdmin:</strong></p>
        <ol>
          <li>وارد DirectAdmin شوید</li>
          <li>بخش <strong>«Advanced Features»</strong> → <strong>«Cronjobs»</strong> را باز کنید</li>
          <li>روی <strong>«Add Cronjob»</strong> کلیک کنید</li>
          <li>در بخش <strong>Command</strong> بنویسید:<br>
            <code>wget -q -O /dev/null "<?= htmlspecialchars($cron_url) ?>"</code>
          </li>
          <li>زمان‌بندی را تنظیم کنید (مثلاً هر ۵ دقیقه: <code>*/5 * * * *</code>)</li>
          <li>ذخیره کنید</li>
        </ol>
      </div>
      <div class="btn-group mt-16">
        <button class="btn btn-green" onclick="runNow()">▶ تست اجرای فوری</button>
      </div>
      <div id="run-output" class="run-output hidden"></div>
    </div>
  </section>

  <form method="post" id="settings-form">
    <input type="hidden" name="action" value="save_settings">

    <!-- Channels -->
    <section id="section-channels" class="card">
      <div class="card-header"><h2>📡 تنظیمات کانال‌ها</h2></div>
      <div class="card-body">
        <div class="form-row">
          <div class="form-group">
            <label>کانال مبدا <span class="hint">(کانال عمومی منبع قیمت)</span></label>
            <input type="text" name="source_channel"
                   value="<?= htmlspecialchars($settings['source_channel'] ?? '') ?>"
                   placeholder="@source_channel یا channel_name" dir="ltr">
          </div>
          <div class="form-group">
            <label>کانال مقصد <span class="hint">(ربات باید ادمین آن باشد)</span></label>
            <input type="text" name="dest_channel"
                   value="<?= htmlspecialchars($settings['dest_channel'] ?? '') ?>"
                   placeholder="@dest_channel" dir="ltr">
          </div>
        </div>
      </div>
    </section>

    <!-- Thresholds -->
    <section id="section-thresholds" class="card">
      <div class="card-header"><h2>📊 آستانه‌های قیمتی</h2></div>
      <div class="card-body">
        <div class="form-row">
          <div class="form-group">
            <label>آستانه اختلاف <span class="hint">(اگر اختلاف بیشتر از این باشد، ارسال می‌شود)</span></label>
            <div class="input-with-unit">
              <input type="number" name="difference_threshold"
                     value="<?= htmlspecialchars($settings['difference_threshold'] ?? '300') ?>"
                     min="0" step="10" id="inp-threshold">
              <span class="unit">تومان</span>
            </div>
          </div>
          <div class="form-group">
            <label>مقدار کسر <span class="hint">(از میانگین کسر می‌شود)</span></label>
            <div class="input-with-unit">
              <input type="number" name="price_deduction"
                     value="<?= htmlspecialchars($settings['price_deduction'] ?? '100') ?>"
                     min="0" step="10" id="inp-deduction">
              <span class="unit">تومان</span>
            </div>
          </div>
        </div>
        <div class="formula-box">
          <div class="formula">
            <span class="formula-label">قیمت ارسالی</span>
            <span class="op">=</span>
            <span class="val">میانگین (خرید + فروش) ÷ ۲</span>
            <span class="op">−</span>
            <span class="val" id="f-deduction"><?= htmlspecialchars($settings['price_deduction'] ?? '100') ?></span>
            <span class="unit">تومان</span>
          </div>
          <p class="formula-note">
            فقط زمانی که اختلاف بیشتر از
            <strong id="f-threshold"><?= htmlspecialchars($settings['difference_threshold'] ?? '300') ?></strong>
            تومان باشد
          </p>
        </div>
      </div>
    </section>

    <!-- Message -->
    <section id="section-message" class="card">
      <div class="card-header"><h2>💬 قالب پیام و دکمه‌ها</h2></div>
      <div class="card-body">
        <div class="form-group">
          <label>قالب پیام <span class="hint">({price} = قیمت با کاما ، {date} = تاریخ شمسی)</span></label>
          <textarea name="message_template" rows="4"
                    id="inp-template"><?= htmlspecialchars($settings['message_template'] ?? '') ?></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>متن دکمه ۱</label>
            <input type="text" name="button1_text" id="inp-btn1"
                   value="<?= htmlspecialchars($settings['button1_text'] ?? 'دانلود اپلیکیشن') ?>">
          </div>
          <div class="form-group">
            <label>لینک دکمه ۱</label>
            <input type="url" name="button1_url"
                   value="<?= htmlspecialchars($settings['button1_url'] ?? '') ?>"
                   placeholder="https://..." dir="ltr">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>متن دکمه ۲</label>
            <input type="text" name="button2_text" id="inp-btn2"
                   value="<?= htmlspecialchars($settings['button2_text'] ?? 'پشتیبانی') ?>">
          </div>
          <div class="form-group">
            <label>لینک دکمه ۲</label>
            <input type="url" name="button2_url"
                   value="<?= htmlspecialchars($settings['button2_url'] ?? '') ?>"
                   placeholder="https://t.me/..." dir="ltr">
          </div>
        </div>

        <!-- Telegram preview -->
        <div class="tg-preview">
          <div class="tg-preview-header">پیش‌نمایش پیام تلگرام</div>
          <div class="tg-message">
            <div class="tg-text" id="preview-text">
              قیمت تتر : <strong>167,500</strong> تومان 💵 USDT<br>
              ─────────────────<br>
              تاریخ: <?= jalali_date('Y/m/d') ?>
            </div>
            <div class="tg-buttons">
              <span class="tg-btn glass-btn" id="preview-btn1">
                <?= htmlspecialchars($settings['button1_text'] ?? 'دانلود اپلیکیشن') ?>
              </span>
              <span class="tg-btn glass-btn" id="preview-btn2">
                <?= htmlspecialchars($settings['button2_text'] ?? 'پشتیبانی') ?>
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Bot -->
    <section id="section-bot" class="card">
      <div class="card-header"><h2>🤖 توکن ربات تلگرام</h2></div>
      <div class="card-body">
        <p class="info-text">
          از <strong>@BotFather</strong> در تلگرام ربات بسازید و توکن را وارد کنید.
          ربات را ادمین کانال مقصد کنید.
        </p>
        <div class="form-group">
          <label>Bot Token</label>
          <input type="text" name="bot_token"
                 value="<?= htmlspecialchars($settings['bot_token'] ?? '') ?>"
                 placeholder="1234567890:ABCdefGHI..." dir="ltr">
        </div>
        <button type="button" class="btn btn-outline" onclick="testBot()">تست توکن</button>
      </div>
    </section>

    <!-- Account -->
    <section id="section-account" class="card">
      <div class="card-header"><h2>🔐 تغییر اطلاعات ورود</h2></div>
      <div class="card-body">
        <div class="form-row">
          <div class="form-group">
            <label>نام کاربری جدید</label>
            <input type="text" name="admin_username"
                   value="<?= htmlspecialchars($settings['admin_username'] ?? 'admin') ?>">
          </div>
          <div class="form-group">
            <label>رمز عبور جدید</label>
            <input type="password" name="admin_password" placeholder="رمز فعلی حفظ می‌شود اگر خالی باشد">
          </div>
        </div>
      </div>
    </section>

    <div class="form-actions">
      <button type="submit" class="btn btn-primary btn-lg">💾 ذخیره همه تنظیمات</button>
    </div>
  </form>

  <!-- Logs -->
  <section id="section-logs" class="card">
    <div class="card-header">
      <h2>📋 لاگ‌های اخیر</h2>
      <a href="<?= $_SERVER['PHP_SELF'] ?>#section-logs" class="btn btn-sm btn-outline">↻ بروزرسانی</a>
    </div>
    <div class="card-body">
      <div class="table-wrapper">
        <table class="log-table">
          <thead>
            <tr>
              <th>زمان</th>
              <th>خرید مبدا</th>
              <th>فروش مبدا</th>
              <th>میانگین</th>
              <th>قیمت مقصد</th>
              <th>اختلاف</th>
              <th>ارسالی</th>
              <th>نتیجه</th>
            </tr>
          </thead>
          <tbody>
            <?php if (empty($logs)): ?>
            <tr><td colspan="8" class="text-center text-muted">هنوز لاگی ثبت نشده</td></tr>
            <?php else: ?>
            <?php foreach ($logs as $log): ?>
            <tr>
              <td><?= htmlspecialchars(substr($log['created_at'] ?? '', 5, 11)) ?></td>
              <td><?= $log['source_buy']  ? number_format($log['source_buy'])  : '—' ?></td>
              <td><?= $log['source_sell'] ? number_format($log['source_sell']) : '—' ?></td>
              <td><?= $log['source_avg']  ? number_format($log['source_avg'])  : '—' ?></td>
              <td><?= $log['dest_price']  ? number_format($log['dest_price'])  : '—' ?></td>
              <td class="<?= ($log['difference'] ?? 0) > ($settings['difference_threshold'] ?? 300) ? 'text-red' : '' ?>">
                <?= $log['difference'] ? number_format($log['difference']) : '—' ?>
              </td>
              <td class="text-green"><?= $log['sent_price'] ? number_format($log['sent_price']) : '—' ?></td>
              <td><span class="action-badge action-<?= htmlspecialchars($log['action'] ?? '') ?>">
                <?= htmlspecialchars($log['action'] ?? '') ?>
              </span></td>
            </tr>
            <?php endforeach; ?>
            <?php endif; ?>
          </tbody>
        </table>
      </div>
    </div>
  </section>

</main>

<script src="assets/main.js"></script>
</body>
</html>
