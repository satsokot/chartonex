package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// ─── Config ────────────────────────────────────────────────────────────────

type Config struct {
	BotToken         string
	SourceChannel    string
	DestChannel      string
	IntervalMin      int
	DiffThreshold    float64
	PriceDeduction   float64
	MsgTemplate      string
	Button1Text      string
	Button1URL       string
	Button2Text      string
	Button2URL       string
}

func loadConfig(path string) (Config, error) {
	cfg := Config{
		IntervalMin:    5,
		DiffThreshold:  300,
		PriceDeduction: 100,
		MsgTemplate:    "قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}",
		Button1Text:    "دانلود اپلیکیشن",
		Button2Text:    "پشتیبانی",
	}
	f, err := os.Open(path)
	if err != nil {
		return cfg, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || line[0] == ';' || line[0] == '#' || line[0] == '[' {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k, v := strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])
		// strip inline comment
		if i := strings.Index(v, " ;"); i >= 0 {
			v = strings.TrimSpace(v[:i])
		}
		switch k {
		case "bot_token":
			cfg.BotToken = v
		case "source_channel":
			cfg.SourceChannel = cleanChannel(v)
		case "dest_channel":
			cfg.DestChannel = cleanChannel(v)
		case "check_interval_minutes":
			if n, err := strconv.Atoi(v); err == nil {
				cfg.IntervalMin = n
			}
		case "difference_threshold":
			if f, err := strconv.ParseFloat(v, 64); err == nil {
				cfg.DiffThreshold = f
			}
		case "price_deduction":
			if f, err := strconv.ParseFloat(v, 64); err == nil {
				cfg.PriceDeduction = f
			}
		case "message_template":
			cfg.MsgTemplate = strings.ReplaceAll(v, `\n`, "\n")
		case "button1_text":
			cfg.Button1Text = v
		case "button1_url":
			cfg.Button1URL = v
		case "button2_text":
			cfg.Button2Text = v
		case "button2_url":
			cfg.Button2URL = v
		}
	}
	return cfg, sc.Err()
}

// ─── State (بدون دیتابیس، فقط state.json) ─────────────────────────────────

type State struct {
	LastSentPrice  float64 `json:"last_sent_price"`
	LastMessageID  int64   `json:"last_message_id"`
	LastSourceBuy  float64 `json:"last_source_buy"`
	LastSourceSell float64 `json:"last_source_sell"`
}

func loadState(path string) State {
	var s State
	b, err := os.ReadFile(path)
	if err == nil {
		json.Unmarshal(b, &s)
	}
	return s
}

func saveState(path string, s State) {
	b, _ := json.MarshalIndent(s, "", "  ")
	os.WriteFile(path, b, 0644)
}

// ─── HTTP ──────────────────────────────────────────────────────────────────

var client = &http.Client{Timeout: 20 * time.Second}

// cleanChannel هر فرمتی از آدرس کانال را به نام خالص تبدیل می‌کند
// https://t.me/cafebtc  →  cafebtc
// @cafebtc              →  cafebtc
// t.me/cafebtc          →  cafebtc
func cleanChannel(v string) string {
	v = strings.TrimSpace(v)
	for _, prefix := range []string{"https://t.me/", "http://t.me/", "https://telegram.me/", "t.me/", "telegram.me/"} {
		if strings.HasPrefix(v, prefix) {
			v = strings.TrimPrefix(v, prefix)
			break
		}
	}
	v = strings.TrimPrefix(v, "@")
	return strings.TrimRight(v, "/")
}

func httpGet(url string) (string, int, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", 0, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
	resp, err := client.Do(req)
	if err != nil {
		return "", 0, err
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	return string(b), resp.StatusCode, err
}

// ─── Channel Scraping ──────────────────────────────────────────────────────

var (
	reMsgDiv = regexp.MustCompile(`(?is)<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>`)
	reBR     = regexp.MustCompile(`(?i)<br\s*/?>`)
	reTag    = regexp.MustCompile(`<[^>]+>`)
	reSpaces = regexp.MustCompile(`[ \t]+`)
	reNum    = regexp.MustCompile(`(?:^|[^\d])(\d{4,})(?:[^\d]|$)`)
)

func fetchMsgs(channel string, limit int) []string {
	channel = strings.TrimPrefix(strings.TrimSpace(channel), "@")
	urls := []string{
		"https://t.me/s/" + channel,
		"https://telegram.me/s/" + channel,
	}
	var html string
	for _, u := range urls {
		body, code, err := httpGet(u)
		logPrintf("fetch %s => http=%d len=%d err=%v", u, code, len(body), err)
		if err == nil && code == 200 && len(body) > 500 {
			html = body
			break
		}
	}
	if html == "" {
		return nil
	}
	matches := reMsgDiv.FindAllStringSubmatch(html, -1)
	var msgs []string
	for i := len(matches) - 1; i >= 0; i-- {
		content := matches[i][1]
		content = reBR.ReplaceAllString(content, "\n")
		content = reTag.ReplaceAllString(content, "")
		content = htmlDecode(content)
		var lines []string
		for _, line := range strings.Split(content, "\n") {
			line = strings.TrimSpace(reSpaces.ReplaceAllString(line, " "))
			if line != "" {
				lines = append(lines, line)
			}
		}
		if txt := strings.Join(lines, "\n"); txt != "" {
			msgs = append(msgs, txt)
			if len(msgs) >= limit {
				break
			}
		}
	}
	return msgs
}

func htmlDecode(s string) string {
	s = strings.ReplaceAll(s, "&amp;", "&")
	s = strings.ReplaceAll(s, "&lt;", "<")
	s = strings.ReplaceAll(s, "&gt;", ">")
	s = strings.ReplaceAll(s, "&quot;", "\"")
	s = strings.ReplaceAll(s, "&#39;", "'")
	s = strings.ReplaceAll(s, "&nbsp;", " ")
	return s
}

func numFrom(s string) (float64, bool) {
	s = strings.NewReplacer(",", "", "٬", "", "،", "", ".", "").Replace(s)
	m := reNum.FindStringSubmatch(s)
	if m == nil {
		return 0, false
	}
	f, err := strconv.ParseFloat(m[1], 64)
	return f, err == nil
}

func parseSource(msgs []string) (buy, sell float64, buyOk, sellOk bool) {
	for _, txt := range msgs {
		for _, line := range strings.Split(txt, "\n") {
			p, ok := numFrom(line)
			if !ok {
				continue
			}
			if !buyOk && strings.Contains(line, "خرید") {
				buy, buyOk = p, true
			}
			if !sellOk && strings.Contains(line, "فروش") {
				sell, sellOk = p, true
			}
			if buyOk && sellOk {
				return
			}
		}
	}
	return
}

// ─── Telegram API ──────────────────────────────────────────────────────────

func tgPost(token, method string, payload map[string]interface{}) (map[string]interface{}, error) {
	b, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "https://api.telegram.org/bot"+token+"/"+method, bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

func tgSend(cfg Config, msgText string, editID int64) (int64, error) {
	var row []interface{}
	if cfg.Button1Text != "" && cfg.Button1URL != "" {
		row = append(row, map[string]string{"text": cfg.Button1Text, "url": cfg.Button1URL})
	}
	if cfg.Button2Text != "" && cfg.Button2URL != "" {
		row = append(row, map[string]string{"text": cfg.Button2Text, "url": cfg.Button2URL})
	}
	pl := map[string]interface{}{
		"chat_id":    "@" + cfg.DestChannel,
		"text":       msgText,
		"parse_mode": "HTML",
	}
	if len(row) > 0 {
		pl["reply_markup"] = map[string]interface{}{"inline_keyboard": []interface{}{row}}
	}
	if editID != 0 {
		pl["message_id"] = editID
		r, err := tgPost(cfg.BotToken, "editMessageText", pl)
		if err == nil {
			if ok, _ := r["ok"].(bool); ok {
				return msgIDFrom(r), nil
			}
		}
		delete(pl, "message_id")
	}
	r, err := tgPost(cfg.BotToken, "sendMessage", pl)
	if err != nil {
		return 0, err
	}
	if ok, _ := r["ok"].(bool); !ok {
		desc, _ := r["description"].(string)
		return 0, fmt.Errorf("Telegram: %s", desc)
	}
	return msgIDFrom(r), nil
}

func msgIDFrom(r map[string]interface{}) int64 {
	if res, ok := r["result"].(map[string]interface{}); ok {
		if mid, ok := res["message_id"].(float64); ok {
			return int64(mid)
		}
	}
	return 0
}

// ─── Jalali Date ───────────────────────────────────────────────────────────

func jalaliNow() string {
	tehran := time.FixedZone("IRST", 3*60*60+30*60)
	now := time.Now().In(tehran)
	y, m, d := now.Year(), int(now.Month()), now.Day()
	n := 365*y + (y+3)/4 - (y+99)/100 + (y+399)/400
	gd := [12]int{0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334}
	if y%4 == 0 && (y%100 != 0 || y%400 == 0) {
		gd[2] = 60
	}
	n += gd[m-1] + d - 1
	jn := n - 79
	jp := jn / 12053
	jn %= 12053
	jy := 979 + 33*jp + 4*(jn/1461)
	jn %= 1461
	if jn >= 366 {
		jy += (jn - 1) / 365
		jn = (jn - 1) % 365
	}
	mi := [12]int{0, 31, 59, 90, 120, 151, 181, 212, 242, 272, 302, 333}
	jm, jd2 := 1, 1
	for i, v := range mi {
		lim := v + 31
		if i >= 6 {
			lim = v + 30
		}
		if jn < lim {
			jm = i + 1
			jd2 = jn - v + 1
			break
		}
	}
	return fmt.Sprintf("%d/%02d/%02d", jy, jm, jd2)
}

// ─── Helpers ───────────────────────────────────────────────────────────────

func fmtPrice(p float64) string {
	s := fmt.Sprintf("%.0f", p)
	n := len(s)
	var b strings.Builder
	for i, c := range s {
		if i > 0 && (n-i)%3 == 0 {
			b.WriteRune(',')
		}
		b.WriteRune(c)
	}
	return b.String()
}

func buildMsg(price float64, tmpl string) string {
	s := strings.ReplaceAll(tmpl, "{price}", fmtPrice(price))
	return strings.ReplaceAll(s, "{date}", jalaliNow())
}

func trunc(s string, n int) string {
	r := []rune(s)
	if len(r) > n {
		return string(r[:n]) + "..."
	}
	return s
}

// ─── Logger ────────────────────────────────────────────────────────────────

var logger *log.Logger

func logPrintf(format string, args ...interface{}) {
	logger.Printf(format, args...)
}

// ─── Startup Checks ────────────────────────────────────────────────────────

// checkInternet: یه سایت عمومی رو پینگ می‌کنه
func checkInternet() bool {
	logPrintf("[1/3] بررسی اتصال اینترنت...")
	_, code, err := httpGet("https://example.com")
	if err != nil || code == 0 {
		logPrintf("      ✗ اینترنت متصل نیست — %v", err)
		return false
	}
	logPrintf("      ✓ اینترنت متصل است (HTTP %d)", code)
	return true
}

// maskToken توکن ربات را برای لاگ ماسک می‌کند
func maskToken(token string) string {
	if len(token) < 10 {
		return "***"
	}
	return token[:6] + "***" + token[len(token)-4:]
}

// maskErrToken توکن را از رشته خطا (که ممکن است URL کامل داشته باشد) حذف می‌کند
func maskErrToken(token, errMsg string) string {
	if token == "" {
		return errMsg
	}
	return strings.ReplaceAll(errMsg, token, maskToken(token))
}

// checkBot: توکن ربات رو با getMe تست می‌کنه
func checkBot(token string) (string, bool) {
	logPrintf("[2/3] بررسی اتصال ربات تلگرام (توکن: %s)...", maskToken(token))
	r, err := tgPost(token, "getMe", map[string]interface{}{})
	if err != nil {
		logPrintf("      ✗ خطا در اتصال به api.telegram.org — %s", maskErrToken(token, err.Error()))
		return "", false
	}
	if ok, _ := r["ok"].(bool); !ok {
		desc, _ := r["description"].(string)
		logPrintf("      ✗ توکن ربات نامعتبر است — %s", desc)
		return "", false
	}
	result, _ := r["result"].(map[string]interface{})
	username, _ := result["username"].(string)
	logPrintf("      ✓ ربات متصل است: @%s", username)
	return username, true
}

// checkTelegram: دسترسی به t.me را تست می‌کنه
func checkTelegram(channel string) bool {
	logPrintf("[3/3] بررسی دسترسی به کانال مبدا...")
	_, code, err := httpGet("https://t.me/s/" + channel)
	if err != nil || code == 0 {
		logPrintf("      ✗ t.me در دسترس نیست — %v", err)
		return false
	}
	logPrintf("      ✓ کانال @%s در دسترس است (HTTP %d)", channel, code)
	return true
}

// sendStartupMsg: پیام شروع به کار را به کانال مقصد ارسال می‌کنه
func sendStartupMsg(cfg Config, botUsername string) {
	text := fmt.Sprintf(
		"🟢 <b>Chartonex شروع به کار کرد</b>\n"+
			"─────────────────\n"+
			"🤖 ربات: @%s\n"+
			"📥 مبدا: @%s\n"+
			"📤 مقصد: @%s\n"+
			"⏱ بازه: هر %d دقیقه\n"+
			"📊 آستانه: %s تومان\n"+
			"🕐 زمان: %s",
		botUsername,
		cfg.SourceChannel,
		cfg.DestChannel,
		cfg.IntervalMin,
		fmtPrice(cfg.DiffThreshold),
		jalaliNow(),
	)
	pl := map[string]interface{}{
		"chat_id":    "@" + cfg.DestChannel,
		"text":       text,
		"parse_mode": "HTML",
	}
	r, err := tgPost(cfg.BotToken, "sendMessage", pl)
	if err != nil {
		logPrintf("      خطا در ارسال پیام شروع: %s", maskErrToken(cfg.BotToken, err.Error()))
		return
	}
	if ok, _ := r["ok"].(bool); ok {
		logPrintf("      ✓ پیام شروع به کار ارسال شد")
	} else {
		desc, _ := r["description"].(string)
		logPrintf("      ✗ ارسال پیام شروع ناموفق: %s", desc)
	}
}

// ─── Core Logic ────────────────────────────────────────────────────────────

func runCycle(cfg Config, state *State) {
	logPrintf("══════════════════════════════════")
	logPrintf("شروع چرخه بررسی — %s", jalaliNow())

	// ① اینترنت
	if !checkInternet() {
		logPrintf("چرخه لغو شد — اینترنت متصل نیست")
		return
	}

	// ② ربات
	_, botOk := checkBot(cfg.BotToken)
	if !botOk {
		logPrintf("چرخه لغو شد — ربات در دسترس نیست")
		return
	}

	// ③ کانال مبدا
	checkTelegram(cfg.SourceChannel)

	// ④ بررسی قیمت
	logPrintf("──────────────────────────────────")
	logPrintf("خواندن قیمت از کانال مبدا...")
	msgs := fetchMsgs(cfg.SourceChannel, 10)
	logPrintf("پیام‌های دریافتی: %d عدد", len(msgs))
	for i, m := range msgs {
		logPrintf("  [%d] %s", i, trunc(m, 100))
	}

	buy, sell, buyOk, sellOk := parseSource(msgs)

	if !buyOk && state.LastSourceBuy > 0 {
		buy, buyOk = state.LastSourceBuy, true
		logPrintf("خرید از حافظه: %.0f", buy)
	}
	if !sellOk && state.LastSourceSell > 0 {
		sell, sellOk = state.LastSourceSell, true
		logPrintf("فروش از حافظه: %.0f", sell)
	}
	if buyOk {
		state.LastSourceBuy = buy
	}
	if sellOk {
		state.LastSourceSell = sell
	}

	if !buyOk && !sellOk {
		logPrintf("✗ قیمت از کانال مبدا دریافت نشد")
		return
	}

	var avg float64
	switch {
	case buyOk && sellOk:
		avg = (buy + sell) / 2
	case buyOk:
		avg = buy
	default:
		avg = sell
	}

	destPrice := state.LastSentPrice
	diff := math.Abs(destPrice - avg)
	logPrintf("خرید: %.0f | فروش: %.0f | میانگین: %.0f", buy, sell, avg)
	logPrintf("قیمت مقصد: %.0f | اختلاف: %.0f | آستانه: %.0f", destPrice, diff, cfg.DiffThreshold)

	if diff <= cfg.DiffThreshold {
		logPrintf("✓ اختلاف کمتر از آستانه — ارسال نشد")
		return
	}

	newPrice := math.Round(avg - cfg.PriceDeduction)
	msgText := buildMsg(newPrice, cfg.MsgTemplate)
	logPrintf("ارسال قیمت جدید: %s تومان ...", fmtPrice(newPrice))

	msgID, err := tgSend(cfg, msgText, state.LastMessageID)
	if err != nil {
		logPrintf("✗ خطا در ارسال: %s", maskErrToken(cfg.BotToken, err.Error()))
		return
	}

	state.LastSentPrice = newPrice
	state.LastMessageID = msgID
	logPrintf("✓ ارسال موفق — قیمت: %s تومان | message_id: %d", fmtPrice(newPrice), msgID)
}

// ─── Main ──────────────────────────────────────────────────────────────────

func main() {
	logFile, err := os.OpenFile("log.txt", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Println("خطا در ایجاد log.txt:", err)
		pause()
		return
	}
	defer logFile.Close()

	logger = log.New(io.MultiWriter(os.Stdout, logFile), "", log.Ldate|log.Ltime|log.Lmsgprefix)

	logPrintf("╔══════════════════════════════════╗")
	logPrintf("║     Chartonex v1.0 راه‌اندازی    ║")
	logPrintf("╚══════════════════════════════════╝")

	cfg, err := loadConfig("config.ini")
	if err != nil {
		logPrintf("✗ فایل config.ini پیدا نشد — %v", err)
		pause()
		return
	}
	if cfg.BotToken == "" || cfg.SourceChannel == "" || cfg.DestChannel == "" {
		logPrintf("✗ bot_token، source_channel و dest_channel را در config.ini وارد کنید")
		pause()
		return
	}

	logPrintf("کانال مبدا  : @%s", cfg.SourceChannel)
	logPrintf("کانال مقصد  : @%s", cfg.DestChannel)
	logPrintf("بازه بررسی  : هر %d دقیقه", cfg.IntervalMin)
	logPrintf("آستانه اختلاف: %s تومان", fmtPrice(cfg.DiffThreshold))
	logPrintf("کسر قیمت    : %s تومان", fmtPrice(cfg.PriceDeduction))
	logPrintf("──────────────────────────────────")

	// بررسی‌های اولیه — تا اتصال برقرار نشه هر 15 ثانیه امتحان می‌کنه
	logPrintf("در حال بررسی اتصال‌ها...")
	var botUsername string
	for attempt := 1; ; attempt++ {
		logPrintf("--- تلاش %d ---", attempt)
		if !checkInternet() {
			logPrintf("      ⏳ %d ثانیه صبر می‌کنم...", 15)
			time.Sleep(15 * time.Second)
			continue
		}
		var botOk bool
		botUsername, botOk = checkBot(cfg.BotToken)
		if !botOk {
			logPrintf("      ⏳ %d ثانیه صبر می‌کنم...", 15)
			time.Sleep(15 * time.Second)
			continue
		}
		checkTelegram(cfg.SourceChannel)
		break
	}

	// پیام شروع به کار
	logPrintf("ارسال پیام شروع به کار به کانال مقصد...")
	sendStartupMsg(cfg, botUsername)
	logPrintf("──────────────────────────────────")

	state := loadState("state.json")

	// اولین چرخه فوری
	runCycle(cfg, &state)
	saveState("state.json", state)

	logPrintf("⏱ بررسی بعدی در %d دقیقه دیگر...", cfg.IntervalMin)

	ticker := time.NewTicker(time.Duration(cfg.IntervalMin) * time.Minute)
	defer ticker.Stop()
	for range ticker.C {
		runCycle(cfg, &state)
		saveState("state.json", state)
		logPrintf("⏱ بررسی بعدی در %d دقیقه دیگر...", cfg.IntervalMin)
	}
}

func pause() {
	fmt.Print("\nPress ENTER to exit...")
	bufio.NewReader(os.Stdin).ReadString('\n')
}
