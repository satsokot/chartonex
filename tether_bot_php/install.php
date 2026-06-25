<?php
$config_file = __DIR__ . '/config.php';
$step = $_POST['step'] ?? ($_GET['step'] ?? '1');
$error = '';
$success = '';

// اگر قبلاً نصب شده، برو به پنل
if (file_exists($config_file) && $step !== 'done') {
    require_once $config_file;
    if (defined('DB_NAME') && DB_NAME !== '') {
        // تست اتصال
        try {
            new PDO("mysql:host=".DB_HOST.";dbname=".DB_NAME, DB_USER, DB_PASS);
            header('Location: index.php'); exit;
        } catch(Exception $e) {}
    }
}

// پردازش فرم نصب
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $step === '2') {
    $db_host   = trim($_POST['db_host']   ?? 'localhost');
    $db_name   = trim($_POST['db_name']   ?? '');
    $db_user   = trim($_POST['db_user']   ?? '');
    $db_pass   = trim($_POST['db_pass']   ?? '');
    $adm_user  = trim($_POST['adm_user']  ?? 'admin');
    $adm_pass  = trim($_POST['adm_pass']  ?? '');
    $adm_pass2 = trim($_POST['adm_pass2'] ?? '');

    if (!$db_name || !$db_user || !$adm_user || !$adm_pass) {
        $error = 'لطفاً همه فیلدها را پر کنید';
    } elseif ($adm_pass !== $adm_pass2) {
        $error = 'رمز عبور و تکرار آن یکسان نیستند';
    } elseif (strlen($adm_pass) < 6) {
        $error = 'رمز عبور باید حداقل ۶ کاراکتر باشد';
    } else {
        // تست اتصال به دیتابیس
        try {
            $pdo = new PDO(
                "mysql:host={$db_host};dbname={$db_name};charset=utf8mb4",
                $db_user, $db_pass,
                [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
            );

            // ساخت جداول
            $pdo->exec("CREATE TABLE IF NOT EXISTS settings (
                `key`       VARCHAR(100) PRIMARY KEY,
                `value`     TEXT,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");

            $pdo->exec("CREATE TABLE IF NOT EXISTS price_logs (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                source_buy  DOUBLE,
                source_sell DOUBLE,
                source_avg  DOUBLE,
                dest_price  DOUBLE,
                difference  DOUBLE,
                sent_price  DOUBLE,
                action      VARCHAR(50) DEFAULT 'no_action',
                message_id  BIGINT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");

            // مقادیر پیش‌فرض تنظیمات
            $defaults = [
                'source_channel'       => '',
                'dest_channel'         => '',
                'difference_threshold' => '300',
                'price_deduction'      => '100',
                'bot_token'            => '',
                'button1_text'         => 'دانلود اپلیکیشن',
                'button1_url'          => '',
                'button2_text'         => 'پشتیبانی',
                'button2_url'          => '',
                'last_sent_message_id' => '',
                'message_template'     => "قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}",
                'cron_token'           => bin2hex(random_bytes(16)),
            ];
            $stmt = $pdo->prepare("INSERT IGNORE INTO settings (`key`,`value`) VALUES (?,?)");
            foreach ($defaults as $k => $v) $stmt->execute([$k, $v]);

            // ذخیره config.php
            $secret = bin2hex(random_bytes(24));
            $config_content = "<?php\n"
                . "// این فایل توسط install.php ساخته شده - دست نزنید\n"
                . "define('DB_HOST',    '" . addslashes($db_host)  . "');\n"
                . "define('DB_NAME',    '" . addslashes($db_name)  . "');\n"
                . "define('DB_USER',    '" . addslashes($db_user)  . "');\n"
                . "define('DB_PASS',    '" . addslashes($db_pass)  . "');\n"
                . "define('DB_CHARSET', 'utf8mb4');\n"
                . "define('ADMIN_USER', '" . addslashes($adm_user) . "');\n"
                . "define('ADMIN_PASS', '" . addslashes($adm_pass) . "');\n"
                . "define('SECRET_KEY', '" . $secret . "');\n";

            if (file_put_contents($config_file, $config_content) === false) {
                $error = 'خطا در نوشتن فایل config.php - دسترسی فایل را بررسی کنید';
            } else {
                $step = 'done';
            }

        } catch (PDOException $e) {
            $msg = $e->getMessage();
            if (str_contains($msg, 'Access denied')) $error = 'نام کاربری یا رمز دیتابیس اشتباه است';
            elseif (str_contains($msg, 'Unknown database')) $error = 'دیتابیس با این نام وجود ندارد';
            elseif (str_contains($msg, "Can't connect")) $error = 'اتصال به MySQL ممکن نیست - هاست را بررسی کنید';
            else $error = 'خطا: ' . htmlspecialchars($msg);
        }
    }
}
?>
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>نصب Chartonex Bot</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Tahoma,Arial,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#161b27;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:40px;width:100%;max-width:520px;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.logo{text-align:center;margin-bottom:24px}
.logo-icon{font-size:48px}
.logo h1{font-size:22px;font-weight:700;margin:8px 0 4px}
.logo p{color:#64748b;font-size:13px}
.steps-bar{display:flex;gap:8px;margin-bottom:28px}
.step-dot{flex:1;height:4px;border-radius:2px;background:rgba(255,255,255,.1)}
.step-dot.active{background:#3b82f6}
.step-dot.done{background:#22c55e}
h2{font-size:17px;font-weight:600;margin-bottom:6px}
.sub{font-size:13px;color:#94a3b8;margin-bottom:24px;line-height:1.7}
.fg{margin-bottom:16px}
.fg label{display:block;font-size:13px;color:#94a3b8;margin-bottom:6px;font-weight:500}
.fg .hint{font-size:11px;color:#64748b;font-weight:400}
input{width:100%;background:#1e2535;border:1px solid rgba(255,255,255,.08);border-radius:8px;color:#e2e8f0;padding:10px 14px;font-size:14px;font-family:inherit;outline:none}
input:focus{border-color:#3b82f6}
.fr{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.btn{width:100%;background:#3b82f6;color:#fff;border:none;border-radius:8px;padding:13px;font-size:15px;font-family:inherit;cursor:pointer;margin-top:8px;font-weight:500}
.btn:hover{background:#2563eb}
.err{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#ef4444;padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:20px}
.sec{background:#1e2535;border-radius:10px;padding:16px 18px;margin-bottom:16px}
.sec-title{font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
.success-box{text-align:center;padding:12px 0}
.success-icon{font-size:56px;margin-bottom:16px}
.success-box h2{font-size:20px;color:#22c55e;margin-bottom:8px}
.success-box p{font-size:14px;color:#94a3b8;margin-bottom:24px;line-height:1.7}
.btn-g{background:#22c55e}.btn-g:hover{background:#16a34a}
.sep{border:none;border-top:1px solid rgba(255,255,255,.06);margin:20px 0}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">💵</div>
    <h1>Chartonex Bot</h1>
    <p>راه‌اندازی پنل مدیریت قیمت تتر</p>
  </div>

  <?php if ($step === 'done'): ?>
  <!-- SUCCESS -->
  <div class="steps-bar">
    <div class="step-dot done"></div>
    <div class="step-dot done"></div>
    <div class="step-dot done"></div>
  </div>
  <div class="success-box">
    <div class="success-icon">✅</div>
    <h2>نصب موفق!</h2>
    <p>دیتابیس اتصال برقرار شد، جداول ساخته شدند و تنظیمات ذخیره شدند.</p>
    <a href="index.php"><button class="btn btn-g">ورود به پنل ادمین ←</button></a>
    <hr class="sep">
    <p style="font-size:12px;color:#64748b">این فایل (install.php) را از روی هاست حذف کنید</p>
  </div>

  <?php else: ?>
  <!-- INSTALL FORM -->
  <div class="steps-bar">
    <div class="step-dot done"></div>
    <div class="step-dot active"></div>
    <div class="step-dot"></div>
  </div>
  <h2>اطلاعات دیتابیس و ادمین</h2>
  <p class="sub">اطلاعات دیتابیسی که در DirectAdmin ساختید را وارد کنید.</p>

  <?php if ($error): ?><div class="err">❌ <?= $error ?></div><?php endif; ?>

  <form method="post">
    <input type="hidden" name="step" value="2">

    <div class="sec">
      <div class="sec-title">🗄 اطلاعات دیتابیس MySQL</div>
      <div class="fg">
        <label>هاست دیتابیس <span class="hint">(معمولاً localhost است)</span></label>
        <input type="text" name="db_host" value="<?= htmlspecialchars($_POST['db_host'] ?? 'localhost') ?>" dir="ltr">
      </div>
      <div class="fg">
        <label>نام دیتابیس</label>
        <input type="text" name="db_name" value="<?= htmlspecialchars($_POST['db_name'] ?? '') ?>" dir="ltr" placeholder="cafebtci_mydb">
      </div>
      <div class="fr">
        <div class="fg">
          <label>نام کاربری دیتابیس</label>
          <input type="text" name="db_user" value="<?= htmlspecialchars($_POST['db_user'] ?? '') ?>" dir="ltr" placeholder="cafebtci_user">
        </div>
        <div class="fg">
          <label>رمز دیتابیس</label>
          <input type="password" name="db_pass" value="<?= htmlspecialchars($_POST['db_pass'] ?? '') ?>" dir="ltr">
        </div>
      </div>
    </div>

    <div class="sec">
      <div class="sec-title">🔐 حساب ادمین پنل</div>
      <div class="fg">
        <label>نام کاربری ادمین</label>
        <input type="text" name="adm_user" value="<?= htmlspecialchars($_POST['adm_user'] ?? 'admin') ?>">
      </div>
      <div class="fr">
        <div class="fg">
          <label>رمز عبور پنل</label>
          <input type="password" name="adm_pass" placeholder="حداقل ۶ کاراکتر">
        </div>
        <div class="fg">
          <label>تکرار رمز عبور</label>
          <input type="password" name="adm_pass2" placeholder="تکرار رمز">
        </div>
      </div>
    </div>

    <button type="submit" class="btn">نصب و راه‌اندازی ←</button>
  </form>
  <?php endif; ?>
</div>
</body>
</html>
