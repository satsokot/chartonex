<?php

/**
 * استخراج قیمت خرید و فروش از پیام کانال مبدا
 * فرمت: 💰#تتر[USDT] 168,100فروش♦️
 *        💰#تتر[USDT] 168,111خرید🔹
 */
function parse_source_prices(array $messages): array {
    $buy = null;
    $sell = null;

    foreach ($messages as $text) {
        $lines = explode("\n", $text);
        foreach ($lines as $line) {
            $price = extract_number($line);
            if ($price === null) continue;

            if ((mb_strpos($line, 'خرید') !== false || stripos($line, 'buy') !== false) && $buy === null) {
                $buy = $price;
            } elseif ((mb_strpos($line, 'فروش') !== false || stripos($line, 'sell') !== false) && $sell === null) {
                $sell = $price;
            }

            if ($buy !== null && $sell !== null) break 2;
        }
    }

    return ['buy' => $buy, 'sell' => $sell];
}

/**
 * استخراج قیمت از پیام کانال مقصد
 * فرمت: قیمت تتر : 167500 تومان 💵 USDT
 */
function parse_dest_price(array $messages): ?float {
    foreach ($messages as $text) {
        $price = extract_number($text);
        if ($price !== null) return $price;
    }
    return null;
}

function calculate_average(?float $buy, ?float $sell): ?float {
    if ($buy !== null && $sell !== null) return ($buy + $sell) / 2;
    if ($buy !== null) return $buy;
    if ($sell !== null) return $sell;
    return null;
}

function extract_number(string $text): ?float {
    // حذف کاما و جداکننده هزارتایی
    $cleaned = str_replace([',', '٬', '،'], '', $text);
    // پیدا کردن اولین عدد ۴+ رقمی
    if (preg_match('/\b(\d{4,})\b/', $cleaned, $m)) {
        return (float)$m[1];
    }
    return null;
}

function build_message(float $price, string $template): string {
    // تاریخ شمسی ساده
    $date = jalali_date('Y/m/d');
    $price_fmt = number_format((int)$price);
    return str_replace(['{price}', '{date}'], [$price_fmt, $date], $template);
}

/**
 * تبدیل ساده تاریخ میلادی به شمسی
 */
function jalali_date(string $format = 'Y/m/d', int $timestamp = 0): string {
    if (!$timestamp) $timestamp = time();
    [$gy, $gm, $gd] = [
        (int)date('Y', $timestamp),
        (int)date('n', $timestamp),
        (int)date('j', $timestamp),
    ];

    $g_d_no = 365 * $gy + (int)(($gy + 3) / 4) - (int)(($gy + 99) / 100)
            + (int)(($gy + 399) / 400);
    $gm_d   = [0, 31, 59 + ($gy % 4 === 0 && ($gy % 100 !== 0 || $gy % 400 === 0) ? 1 : 0),
               90, 120, 151, 181, 212, 243, 273, 304, 334];
    $g_d_no += $gm_d[$gm - 1] + $gd - 1;

    $j_d_no = $g_d_no - 79;
    $j_np   = (int)($j_d_no / 12053);
    $j_d_no %= 12053;
    $jy     = 979 + 33 * $j_np + 4 * (int)($j_d_no / 1461);
    $j_d_no %= 1461;

    if ($j_d_no >= 366) {
        $jy    += (int)(($j_d_no - 1) / 365);
        $j_d_no = ($j_d_no - 1) % 365;
    }

    $j_mi = [0, 31, 59, 90, 120, 151, 181, 212, 242, 272, 302, 333];
    $jm   = 0;
    foreach ($j_mi as $i => $v) {
        if ($j_d_no < ($i < 6 ? $v + 31 : $v + 30)) {
            $jm = $i + 1;
            $jd = $j_d_no - $v + 1;
            break;
        }
    }

    return str_replace(
        ['Y', 'm', 'd'],
        [$jy, str_pad((string)$jm, 2, '0', STR_PAD_LEFT), str_pad((string)$jd, 2, '0', STR_PAD_LEFT)],
        $format
    );
}
