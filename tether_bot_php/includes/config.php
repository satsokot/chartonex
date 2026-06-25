<?php
define('APP_VERSION', '1.0.0');
define('DB_PATH', __DIR__ . '/../data/tether_bot.db');
define('DATA_DIR', __DIR__ . '/../data/');

// Session
if (session_status() === PHP_SESSION_NONE) {
    session_name('chartonex_admin');
    session_start();
}

// Timezone
date_default_timezone_set('Asia/Tehran');

// Error reporting (غیرفعال در production)
error_reporting(0);
ini_set('display_errors', 0);
