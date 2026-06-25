<?php
require_once __DIR__ . '/config.php';

// ===== SETTINGS =====

function _load_settings(): array {
    if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);
    if (!file_exists(SETTINGS_FILE)) return _default_settings();
    $data = json_decode(file_get_contents(SETTINGS_FILE), true);
    return is_array($data) ? array_merge(_default_settings(), $data) : _default_settings();
}

function _save_settings(array $data): void {
    if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);
    file_put_contents(SETTINGS_FILE, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

function _default_settings(): array {
    return [
        'source_channel'         => '',
        'dest_channel'           => '',
        'difference_threshold'   => '300',
        'price_deduction'        => '100',
        'check_interval_minutes' => '5',
        'bot_token'              => '',
        'button1_text'           => 'دانلود اپلیکیشن',
        'button1_url'            => '',
        'button2_text'           => 'پشتیبانی',
        'button2_url'            => '',
        'last_sent_message_id'   => '',
        'message_template'       => "قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}",
        'admin_username'         => 'admin',
        'admin_password'         => 'admin123',
        'cron_token'             => bin2hex(random_bytes(16)),
    ];
}

function setting_get(string $key, string $default = ''): string {
    static $cache = null;
    if ($cache === null) $cache = _load_settings();
    return isset($cache[$key]) ? (string)$cache[$key] : $default;
}

function setting_set(string $key, string $value): void {
    $data = _load_settings();
    $data[$key] = $value;
    _save_settings($data);
}

function settings_all(): array {
    return _load_settings();
}

// ===== LOGS =====

function log_insert(array $entry): void {
    if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);
    $logs = logs_get(200);
    array_unshift($logs, array_merge($entry, [
        'id'         => time(),
        'created_at' => date('Y-m-d H:i:s'),
    ]));
    $logs = array_slice($logs, 0, 200);
    file_put_contents(LOGS_FILE, json_encode($logs, JSON_UNESCAPED_UNICODE));
}

function logs_get(int $limit = 50): array {
    if (!file_exists(LOGS_FILE)) return [];
    $data = json_decode(file_get_contents(LOGS_FILE), true);
    $data = is_array($data) ? $data : [];
    return array_slice($data, 0, $limit);
}
