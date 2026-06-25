<?php
ob_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "<h2>PHP Version: " . PHP_VERSION . "</h2>";
echo "<h3>Extensions:</h3><ul>";
echo "<li>cURL: "    . (extension_loaded('curl')    ? '✅' : '❌') . "</li>";
echo "<li>mbstring: ". (extension_loaded('mbstring')? '✅' : '❌') . "</li>";
echo "<li>JSON: "    . (extension_loaded('json')    ? '✅' : '❌') . "</li>";
echo "</ul>";

$data_dir = __DIR__ . '/data/';
if (!is_dir($data_dir)) mkdir($data_dir, 0755, true);
echo "<h3>data/ folder writable: " . (is_writable($data_dir) ? '✅' : '❌') . "</h3>";

echo "<h3>Loading includes...</h3>";
try {
    require_once __DIR__ . '/includes/config.php';
    echo "config.php: ✅<br>";
    require_once __DIR__ . '/includes/db.php';
    echo "db.php: ✅<br>";
    require_once __DIR__ . '/includes/parser.php';
    echo "parser.php: ✅<br>";
    require_once __DIR__ . '/includes/telegram.php';
    echo "telegram.php: ✅<br>";
    require_once __DIR__ . '/includes/auth.php';
    echo "auth.php: ✅<br>";

    $s = settings_all();
    echo "<h3>Settings loaded ✅ (admin: " . htmlspecialchars($s['admin_username']) . ")</h3>";
    echo "<p style='color:green'>همه چیز درسته! حالا index.php را باز کنید.</p>";
} catch (Throwable $e) {
    echo "<h3 style='color:red'>ERROR: " . $e->getMessage() . "</h3>";
    echo "<pre>" . $e->getTraceAsString() . "</pre>";
}
ob_end_flush();
