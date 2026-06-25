<?php
require_once __DIR__ . '/db.php';

function is_logged_in(): bool {
    return !empty($_SESSION['admin_logged_in']);
}

function require_login(): void {
    if (!is_logged_in()) {
        header('Location: /tether_bot/index.php');
        exit;
    }
}

function try_login(string $username, string $password): bool {
    $u = setting_get('admin_username', 'admin');
    $p = setting_get('admin_password', 'admin123');
    if ($username === $u && $password === $p) {
        $_SESSION['admin_logged_in'] = true;
        return true;
    }
    return false;
}

function do_logout(): void {
    $_SESSION = [];
    session_destroy();
}
