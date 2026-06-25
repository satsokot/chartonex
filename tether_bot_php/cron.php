<?php
/**
 * این فایل توسط Cron Job هاست اجرا می‌شود
 * آدرس برای cron: php /path/to/cron.php
 * یا از طریق URL: https://site.com/tether_bot/cron.php?token=CRON_TOKEN
 */

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/telegram.php';
require_once __DIR__ . '/includes/parser.php';

// --- تأیید هویت اگر از طریق URL فراخوانی می‌شود ---
if (PHP_SAPI !== 'cli') {
    $token = $_GET['token'] ?? '';
    $cron_token = setting_get('cron_token');
    if (empty($cron_token) || $token !== $cron_token) {
        http_response_code(403);
        die('Forbidden');
    }
}

// --- بارگذاری تنظیمات ---
$source_channel  = setting_get('source_channel');
$dest_channel    = setting_get('dest_channel');
$bot_token       = setting_get('bot_token');
$threshold       = (float)setting_get('difference_threshold', '300');
$deduction       = (float)setting_get('price_deduction', '100');
$template        = setting_get('message_template');
$btn1_text       = setting_get('button1_text');
$btn1_url        = setting_get('button1_url');
$btn2_text       = setting_get('button2_text');
$btn2_url        = setting_get('button2_url');
$last_msg_id_str = setting_get('last_sent_message_id');
$last_msg_id     = $last_msg_id_str ? (int)$last_msg_id_str : null;

$log = ['action' => 'no_action'];

if (!$source_channel || !$dest_channel || !$bot_token) {
    $log['action'] = 'config_missing';
    log_insert($log);
    echo "config_missing\n";
    exit;
}

// --- ۱. خواندن کانال مبدا ---
$source_msgs = fetch_channel_messages($source_channel, 10);
if (empty($source_msgs)) {
    $log['action'] = 'parse_error_source';
    log_insert($log);
    echo "cannot_read_source\n";
    exit;
}

$parsed  = parse_source_prices($source_msgs);
$buy     = $parsed['buy'];
$sell    = $parsed['sell'];
$avg     = calculate_average($buy, $sell);

$log['source_buy']  = $buy;
$log['source_sell'] = $sell;
$log['source_avg']  = $avg;

if ($avg === null) {
    $log['action'] = 'parse_error_source';
    log_insert($log);
    echo "cannot_parse_prices\n";
    exit;
}

// --- ۲. خواندن کانال مقصد ---
$dest_msgs  = fetch_channel_messages($dest_channel, 3);
$dest_price = parse_dest_price($dest_msgs);
$log['dest_price'] = $dest_price;

if ($dest_price === null) {
    $log['action'] = 'parse_error_dest';
    log_insert($log);
    echo "cannot_parse_dest\n";
    exit;
}

// --- ۳. مقایسه ---
$diff       = abs($dest_price - $avg);
$log['difference'] = $diff;

echo "avg={$avg} dest={$dest_price} diff={$diff} threshold={$threshold}\n";

if ($diff <= $threshold) {
    $log['action'] = 'no_action';
    log_insert($log);
    echo "no_action (diff within threshold)\n";
    exit;
}

// --- ۴. محاسبه و ارسال قیمت جدید ---
$new_price = round($avg - $deduction);
$message   = build_message($new_price, $template);
$log['sent_price'] = $new_price;

$result = send_or_edit_message(
    $bot_token, $dest_channel, $message,
    $btn1_text, $btn1_url, $btn2_text, $btn2_url,
    $last_msg_id
);

if ($result['ok'] ?? false) {
    $new_id = $result['result']['message_id'] ?? null;
    setting_set('last_sent_message_id', (string)($new_id ?? ''));
    $log['action']     = 'sent';
    $log['message_id'] = $new_id;
    echo "sent price={$new_price} message_id={$new_id}\n";
} else {
    $log['action'] = 'send_error';
    echo "send_error: " . ($result['description'] ?? 'unknown') . "\n";
}

log_insert($log);
