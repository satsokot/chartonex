<?php
require_once __DIR__ . '/config.php';

// احراز هویت
if (PHP_SAPI !== 'cli') {
    try {
        $pdo_tmp = new PDO("mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8mb4", DB_USER, DB_PASS, [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
        $tok = $pdo_tmp->query("SELECT `value` FROM settings WHERE `key`='cron_token'")->fetchColumn();
        if (empty($tok) || ($_GET['token'] ?? '') !== $tok) { http_response_code(403); die('Forbidden'); }
    } catch(Exception $e) { die('DB Error'); }
}

run_check();

function run_check(): void {
    $pdo = new PDO(
        "mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8mb4",
        DB_USER, DB_PASS,
        [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]
    );

    function qget(PDO $pdo, string $k): string {
        $r = $pdo->prepare("SELECT `value` FROM settings WHERE `key`=?");
        $r->execute([$k]); $row = $r->fetch();
        return $row ? (string)$row['value'] : '';
    }
    function qset(PDO $pdo, string $k, string $v): void {
        $pdo->prepare("INSERT INTO settings (`key`,`value`) VALUES (?,?) ON DUPLICATE KEY UPDATE `value`=?")->execute([$k,$v,$v]);
    }
    function log_it(PDO $pdo, array $d): void {
        $pdo->prepare("INSERT INTO price_logs (source_buy,source_sell,source_avg,dest_price,difference,sent_price,action,message_id)
            VALUES (?,?,?,?,?,?,?,?)")->execute([
            $d['source_buy']??null, $d['source_sell']??null, $d['source_avg']??null,
            $d['dest_price']??null, $d['difference']??null,  $d['sent_price']??null,
            $d['action']??'no_action', $d['message_id']??null
        ]);
    }

    $src_ch  = qget($pdo, 'source_channel');
    $dst_ch  = qget($pdo, 'dest_channel');
    $token   = qget($pdo, 'bot_token');
    $thresh  = (float)(qget($pdo, 'difference_threshold') ?: 300);
    $deduct  = (float)(qget($pdo, 'price_deduction')      ?: 100);
    $tmpl    = qget($pdo, 'message_template') ?: "قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}";
    $btn1t   = qget($pdo, 'button1_text');
    $btn1u   = qget($pdo, 'button1_url');
    $btn2t   = qget($pdo, 'button2_text');
    $btn2u   = qget($pdo, 'button2_url');
    $last_id = qget($pdo, 'last_sent_message_id');

    if (!$src_ch || !$dst_ch || !$token) {
        echo "config_missing\n"; log_it($pdo, ['action'=>'config_missing']); return;
    }

    // ── خواندن کانال مبدا ──────────────────────────────────────────────────
    echo "src_channel={$src_ch}\n";
    $src_msgs = tg_channel_msgs($src_ch, 10);
    echo "src_msgs_count=".count($src_msgs)."\n";
    foreach ($src_msgs as $i => $m) echo "src[{$i}]: ".mb_substr($m, 0, 100)."\n";

    [$buy, $sell] = parse_source($src_msgs);

    // اگر از scraping نشد، از قیمت‌های ذخیره‌شده استفاده کن
    if ($buy  === null) { $v = qget($pdo,'last_source_buy');  if ($v !== '') { $buy  = (float)$v; echo "buy_fallback={$buy}\n"; } }
    if ($sell === null) { $v = qget($pdo,'last_source_sell'); if ($v !== '') { $sell = (float)$v; echo "sell_fallback={$sell}\n"; } }

    // اگر موفق شدیم قیمت جدید بگیریم، ذخیره کن
    if ($buy  !== null) qset($pdo, 'last_source_buy',  (string)$buy);
    if ($sell !== null) qset($pdo, 'last_source_sell', (string)$sell);

    echo "buy={$buy} sell={$sell}\n";
    $avg = ($buy !== null && $sell !== null) ? ($buy+$sell)/2 : ($buy ?? $sell);

    if ($avg === null) {
        echo "parse_error_source\n";
        log_it($pdo, ['source_buy'=>$buy,'source_sell'=>$sell,'action'=>'parse_error_source']); return;
    }

    // ── قیمت فعلی کانال مقصد (از DB نه scraping) ─────────────────────────
    $dest_str   = qget($pdo, 'last_sent_price');
    $dest_price = $dest_str !== '' ? (float)$dest_str : null;

    if ($dest_price === null) {
        // اولین بار: از لاگ‌ها بخوان
        $row = $pdo->query("SELECT sent_price FROM price_logs WHERE action='sent' ORDER BY id DESC LIMIT 1")->fetch();
        $dest_price = $row && $row['sent_price'] ? (float)$row['sent_price'] : 0;
        echo "first_run dest_price={$dest_price}\n";
    }

    $diff = abs($dest_price - $avg);
    echo "avg={$avg} dest={$dest_price} diff={$diff} threshold={$thresh}\n";

    if ($diff <= $thresh) {
        echo "no_action\n";
        log_it($pdo, ['source_buy'=>$buy,'source_sell'=>$sell,'source_avg'=>$avg,'dest_price'=>$dest_price,'difference'=>$diff,'action'=>'no_action']); return;
    }

    $new_price = round($avg - $deduct);
    $msg_text  = build_msg($new_price, $tmpl);
    $edit_id   = $last_id ? (int)$last_id : null;

    $result = tg_send($token, $dst_ch, $msg_text, $btn1t, $btn1u, $btn2t, $btn2u, $edit_id);

    if ($result['ok'] ?? false) {
        $new_msg_id = $result['result']['message_id'] ?? null;
        qset($pdo, 'last_sent_message_id', (string)($new_msg_id ?? ''));
        qset($pdo, 'last_sent_price', (string)$new_price); // ذخیره قیمت ارسال‌شده
        echo "sent price={$new_price} id={$new_msg_id}\n";
        log_it($pdo, ['source_buy'=>$buy,'source_sell'=>$sell,'source_avg'=>$avg,'dest_price'=>$dest_price,'difference'=>$diff,'sent_price'=>$new_price,'action'=>'sent','message_id'=>$new_msg_id]);
    } else {
        echo "send_error: ".($result['description']??'unknown')."\n";
        log_it($pdo, ['source_buy'=>$buy,'source_sell'=>$sell,'source_avg'=>$avg,'dest_price'=>$dest_price,'difference'=>$diff,'sent_price'=>$new_price,'action'=>'send_error']);
    }
}

// ── خواندن پیام‌های کانال ─────────────────────────────────────────────────
// چند URL موازی امتحان می‌کند: t.me و telegram.me
function tg_channel_msgs(string $channel, int $limit): array {
    $channel = ltrim(trim($channel), '@');
    $urls = [
        "https://t.me/s/{$channel}",
        "https://telegram.me/s/{$channel}",
    ];
    $html = false;
    foreach ($urls as $url) {
        [$res, $code, $err] = http_fetch_dbg($url);
        echo "fetch {$url} http={$code} len=".strlen($res ?: '')." err={$err}\n";
        if ($res && $code === 200 && strlen($res) > 500) { $html = $res; break; }
    }
    if (!$html) return [];

    preg_match_all('/<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)<\/div>/is', $html, $m);
    $msgs = [];
    if (!empty($m[1])) {
        foreach (array_reverse($m[1]) as $item) {
            $item   = preg_replace('/<br\s*\/?>/i', "\n", $item);
            $decoded = html_entity_decode(strip_tags($item), ENT_QUOTES|ENT_HTML5, 'UTF-8');
            $txt    = trim(preg_replace('/[ \t]+/', ' ', $decoded));
            if ($txt) { $msgs[] = $txt; if (count($msgs) >= $limit) break; }
        }
    }
    return $msgs;
}

function parse_source(array $msgs): array {
    $buy = $sell = null;
    foreach ($msgs as $txt) {
        foreach (explode("\n", $txt) as $line) {
            $p = num_from($line);
            if ($p === null) continue;
            if (mb_strpos($line,'خرید')!==false && $buy===null)  $buy  = $p;
            if (mb_strpos($line,'فروش')!==false && $sell===null) $sell = $p;
            if ($buy!==null && $sell!==null) break 2;
        }
    }
    return [$buy, $sell];
}

function num_from(string $t): ?float {
    $c = str_replace([',','٬','،','.'], '', $t);
    return preg_match('/(?<!\d)(\d{4,})(?!\d)/', $c, $m) ? (float)$m[1] : null;
}

function build_msg(float $price, string $tpl): string {
    date_default_timezone_set('Asia/Tehran');
    return str_replace(['{price}','{date}'], [number_format((int)$price), jalali_now()], $tpl);
}

function jalali_now(): string {
    $t = time(); [$y,$m,$d] = [(int)date('Y',$t),(int)date('n',$t),(int)date('j',$t)];
    $n = 365*$y+(int)(($y+3)/4)-(int)(($y+99)/100)+(int)(($y+399)/400);
    $gd=[0,31,59+($y%4==0&&($y%100!=0||$y%400==0)?1:0),90,120,151,181,212,243,273,304,334];
    $n+=$gd[$m-1]+$d-1; $jn=$n-79; $jp=(int)($jn/12053); $jn%=12053;
    $jy=979+33*$jp+4*(int)($jn/1461); $jn%=1461;
    if($jn>=366){$jy+=(int)(($jn-1)/365);$jn=($jn-1)%365;}
    $mi=[0,31,59,90,120,151,181,212,242,272,302,333]; $jm=$jd=0;
    foreach($mi as $i=>$v){$lim=$i<6?$v+31:$v+30; if($jn<$lim){$jm=$i+1;$jd=$jn-$v+1;break;}}
    return $jy.'/'.str_pad($jm,2,'0',STR_PAD_LEFT).'/'.str_pad($jd,2,'0',STR_PAD_LEFT);
}

function tg_send(string $tok, string $ch, string $txt, string $b1t, string $b1u, string $b2t, string $b2u, ?int $edit): array {
    $row = []; if($b1t&&$b1u) $row[]=['text'=>$b1t,'url'=>$b1u]; if($b2t&&$b2u) $row[]=['text'=>$b2t,'url'=>$b2u];
    $pl = ['chat_id'=>$ch,'text'=>$txt,'parse_mode'=>'HTML'];
    if($row) $pl['reply_markup']=['inline_keyboard'=>[$row]];
    $base = "https://api.telegram.org/bot{$tok}";
    if ($edit) { $pl['message_id']=$edit; $r=tg_post("{$base}/editMessageText",$pl); if(!($r['ok']??false)&&in_array($r['error_code']??0,[400,404])){unset($pl['message_id']);$r=tg_post("{$base}/sendMessage",$pl);} return $r; }
    return tg_post("{$base}/sendMessage",$pl);
}

function tg_post(string $url, array $data): array {
    $ch = curl_init($url);
    curl_setopt_array($ch,[CURLOPT_POST=>1,CURLOPT_POSTFIELDS=>json_encode($data),CURLOPT_HTTPHEADER=>['Content-Type: application/json'],CURLOPT_RETURNTRANSFER=>1,CURLOPT_TIMEOUT=>15]);
    $res=curl_exec($ch); $err=curl_error($ch); curl_close($ch);
    if($err) return ['ok'=>false,'description'=>$err];
    return json_decode($res,true)?:['ok'=>false,'description'=>'Invalid JSON'];
}

function http_fetch(string $url): string|false {
    [$r] = http_fetch_dbg($url); return $r;
}
function http_fetch_dbg(string $url): array {
    $ch=curl_init($url);
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>1,CURLOPT_TIMEOUT=>20,CURLOPT_USERAGENT=>'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',CURLOPT_FOLLOWLOCATION=>1,CURLOPT_SSL_VERIFYPEER=>1]);
    $r=curl_exec($ch); $code=curl_getinfo($ch,CURLINFO_HTTP_CODE); $err=curl_error($ch); curl_close($ch);
    return [$r ?: false, $code, $err];
}
