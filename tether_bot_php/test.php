<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "<h2>PHP Version: " . PHP_VERSION . "</h2>";
echo "<h3>Extensions:</h3><ul>";
echo "<li>SQLite3: " . (extension_loaded('sqlite3') ? '✅' : '❌') . "</li>";
echo "<li>cURL: "    . (extension_loaded('curl')    ? '✅' : '❌') . "</li>";
echo "<li>mbstring: ". (extension_loaded('mbstring')? '✅' : '❌') . "</li>";
echo "</ul>";

// Test data folder write
$data_dir = __DIR__ . '/data/';
if (!is_dir($data_dir)) mkdir($data_dir, 0755, true);
$writable = is_writable($data_dir);
echo "<h3>data/ folder writable: " . ($writable ? '✅' : '❌') . "</h3>";

// Test SQLite
if (extension_loaded('sqlite3')) {
    try {
        $db = new SQLite3($data_dir . 'test.db');
        $db->exec("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY)");
        echo "<h3>SQLite3 write test: ✅</h3>";
        $db->close();
        unlink($data_dir . 'test.db');
    } catch (Exception $e) {
        echo "<h3>SQLite3 error: " . $e->getMessage() . "</h3>";
    }
}

// Test includes
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
    echo "<h3>All includes OK ✅</h3>";

    $db = get_db();
    echo "<h3>Database initialized ✅</h3>";
    echo "<p>Admin user: " . setting_get('admin_username') . "</p>";
} catch (Throwable $e) {
    echo "<h3 style='color:red'>ERROR: " . $e->getMessage() . "</h3>";
    echo "<pre>" . $e->getTraceAsString() . "</pre>";
}
