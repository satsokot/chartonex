<?php
ob_start();

define('DATA_DIR', __DIR__ . '/../data/');
define('SETTINGS_FILE', DATA_DIR . 'settings.json');
define('LOGS_FILE',     DATA_DIR . 'logs.json');

date_default_timezone_set('Asia/Tehran');
error_reporting(0);
ini_set('display_errors', 0);

if (session_status() === PHP_SESSION_NONE) {
    session_name('chartonex_admin');
    session_start();
}
