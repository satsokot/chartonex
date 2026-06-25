<?php
require_once __DIR__ . '/config.php';

function get_db(): SQLite3 {
    static $db = null;
    if ($db === null) {
        if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0755, true);
        $db = new SQLite3(DB_PATH);
        $db->exec('PRAGMA journal_mode=WAL');
        _init_tables($db);
    }
    return $db;
}

function _init_tables(SQLite3 $db): void {
    $db->exec("CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    )");

    $db->exec("CREATE TABLE IF NOT EXISTS price_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_buy REAL,
        source_sell REAL,
        source_avg REAL,
        dest_price REAL,
        difference REAL,
        sent_price REAL,
        action TEXT DEFAULT 'no_action',
        message_id INTEGER,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )");

    // Default settings
    $defaults = [
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

    foreach ($defaults as $key => $value) {
        $stmt = $db->prepare("INSERT OR IGNORE INTO settings (key, value) VALUES (:k, :v)");
        $stmt->bindValue(':k', $key);
        $stmt->bindValue(':v', $value);
        $stmt->execute();
    }
}

function setting_get(string $key, string $default = ''): string {
    $db = get_db();
    $stmt = $db->prepare("SELECT value FROM settings WHERE key = :k");
    $stmt->bindValue(':k', $key);
    $res = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    return $res ? (string)$res['value'] : $default;
}

function setting_set(string $key, string $value): void {
    $db = get_db();
    $stmt = $db->prepare("INSERT OR REPLACE INTO settings (key, value, updated_at)
                          VALUES (:k, :v, datetime('now'))");
    $stmt->bindValue(':k', $key);
    $stmt->bindValue(':v', $value);
    $stmt->execute();
}

function log_insert(array $data): void {
    $db = get_db();
    $stmt = $db->prepare("INSERT INTO price_logs
        (source_buy, source_sell, source_avg, dest_price, difference, sent_price, action, message_id)
        VALUES (:buy, :sell, :avg, :dest, :diff, :sent, :action, :mid)");
    $stmt->bindValue(':buy',    $data['source_buy']  ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':sell',   $data['source_sell'] ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':avg',    $data['source_avg']  ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':dest',   $data['dest_price']  ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':diff',   $data['difference']  ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':sent',   $data['sent_price']  ?? null, SQLITE3_FLOAT);
    $stmt->bindValue(':action', $data['action']      ?? 'no_action');
    $stmt->bindValue(':mid',    $data['message_id']  ?? null, SQLITE3_INTEGER);
    $stmt->execute();
}

function logs_get(int $limit = 50): array {
    $db = get_db();
    $res = $db->query("SELECT * FROM price_logs ORDER BY id DESC LIMIT $limit");
    $rows = [];
    while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
        $rows[] = $row;
    }
    return $rows;
}
