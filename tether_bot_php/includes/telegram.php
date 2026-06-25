<?php

/**
 * دریافت آخرین پیام‌های یک کانال عمومی تلگرام
 * از صفحه وب t.me/s/ استخراج می‌شود
 */
function fetch_channel_messages(string $channel, int $limit = 5): array {
    $channel = ltrim(trim($channel), '@');
    if (empty($channel)) return [];

    $url = "https://t.me/s/{$channel}";
    $html = http_get($url);
    if (!$html) return [];

    // پیام‌ها را از HTML استخراج می‌کنیم
    preg_match_all('/<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)<\/div>/is', $html, $matches);
    $messages = [];
    if (!empty($matches[1])) {
        foreach (array_reverse($matches[1]) as $msg) {
            // حذف تگ‌های HTML
            $text = html_entity_decode(strip_tags($msg), ENT_QUOTES | ENT_HTML5, 'UTF-8');
            $text = trim(preg_replace('/\s+/', ' ', $text));
            if (!empty($text)) {
                $messages[] = $text;
                if (count($messages) >= $limit) break;
            }
        }
    }
    return $messages;
}

/**
 * ارسال یا ویرایش پیام در کانال مقصد با دکمه‌های inline
 */
function send_or_edit_message(
    string $bot_token,
    string $channel,
    string $text,
    string $btn1_text = '',
    string $btn1_url  = '',
    string $btn2_text = '',
    string $btn2_url  = '',
    ?int   $edit_id   = null
): array {
    $keyboard = [];
    $row = [];
    if ($btn1_text && $btn1_url) $row[] = ['text' => $btn1_text, 'url' => $btn1_url];
    if ($btn2_text && $btn2_url) $row[] = ['text' => $btn2_text, 'url' => $btn2_url];
    if ($row) $keyboard = [$row];

    $payload = [
        'chat_id'      => $channel,
        'text'         => $text,
        'parse_mode'   => 'HTML',
    ];
    if ($keyboard) {
        $payload['reply_markup'] = ['inline_keyboard' => $keyboard];
    }

    $base = "https://api.telegram.org/bot{$bot_token}";

    if ($edit_id) {
        $payload['message_id'] = $edit_id;
        $result = tg_post("{$base}/editMessageText", $payload);
        // اگر پیام قدیمی پیدا نشد، پیام جدید بفرست
        if (!$result['ok'] && isset($result['error_code']) && in_array($result['error_code'], [400, 404])) {
            unset($payload['message_id']);
            $result = tg_post("{$base}/sendMessage", $payload);
        }
    } else {
        $result = tg_post("{$base}/sendMessage", $payload);
    }

    return $result;
}

function test_bot(string $bot_token): array {
    $result = http_get_json("https://api.telegram.org/bot{$bot_token}/getMe");
    if ($result && $result['ok']) {
        return ['ok' => true, 'username' => $result['result']['username'] ?? ''];
    }
    return ['ok' => false, 'error' => $result['description'] ?? 'خطا'];
}

function tg_post(string $url, array $data): array {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($data),
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);
    $res  = curl_exec($ch);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($err) return ['ok' => false, 'description' => $err];
    $json = json_decode($res, true);
    return $json ?: ['ok' => false, 'description' => 'Invalid JSON'];
}

function http_get(string $url): string|false {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_USERAGENT      => 'Mozilla/5.0 (compatible)',
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_FOLLOWLOCATION => true,
    ]);
    $res = curl_exec($ch);
    curl_close($ch);
    return $res;
}

function http_get_json(string $url): array|null {
    $res = http_get($url);
    if (!$res) return null;
    return json_decode($res, true);
}
