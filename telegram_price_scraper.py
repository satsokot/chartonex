"""
ChartoneX - Telegram USDT Price Scraper
A modern Windows GUI application for extracting USDT buy/sell prices from Telegram channels
"""

import customtkinter as ctk
import json
import os
import re
import threading
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
import tkinter as tk


# ── App Settings ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_FILE = "channels.json"
SETTINGS_FILE = "settings.json"

# ── Color Palette ─────────────────────────────────────────────────────────────
C = {
    "bg":         "#050810",
    "bg2":        "#090F1E",
    "card":       "#0B1525",
    "card2":      "#0E1A2E",
    "input":      "#101E33",
    "border":     "#162440",
    "border2":    "#1E3358",
    "blue":       "#4F8EF7",
    "blue_hov":   "#3A7AE8",
    "blue_dim":   "#0A1B3A",
    "blue_glow":  "#1A3A70",
    "teal":       "#00C9A7",
    "teal_hov":   "#00B396",
    "teal_dim":   "#041E17",
    "buy":        "#00D47E",
    "buy_hov":    "#00BA6E",
    "buy_dim":    "#051A0E",
    "buy_glow":   "#0A3520",
    "sell":       "#FF4060",
    "sell_hov":   "#E82F50",
    "sell_dim":   "#200610",
    "sell_glow":  "#3D0B1A",
    "gold":       "#FFB800",
    "gold_dim":   "#1F1600",
    "gold_glow":  "#3D2C00",
    "text":       "#DCE8FF",
    "text2":      "#5A78A8",
    "text3":      "#253C62",
    "red":        "#FF4060",
    "red_hov":    "#E02050",
    "green":      "#00D47E",
    "sidebar":    "#060C1A",
    "sidebar_hov":"#0C1628",
    "active_bar": "#4F8EF7",
    "accent":     "#4F8EF7",
    "purple":     "#7C3AED",
    "purple_dim": "#150B2E",
}


# ── Database Helpers ──────────────────────────────────────────────────────────
def load_channels():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_channels(channels):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)


def load_settings():
    defaults = {
        "api_id": "", "api_hash": "", "phone": "", "interval": 60,
        "bot_token": "", "dest_channel": "",
        "msg_template": "نرخ تتر: {قیمت} تومان\nتاریخ: {تاریخ}\nساعت: {ساعت}",
        "inline_buttons": "",
        "calc_source": "", "calc_dest": "",
        "calc_threshold": "500", "calc_deduction": "200",
    }
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            defaults.update(data)
            return defaults
    except Exception:
        return defaults


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# ── Price Extraction ──────────────────────────────────────────────────────────
FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
NUM = r'([\d۰-۹٠-٩][،,\d۰-۹٠-٩\.]*)'

PRICE_PATTERNS = [
    # ── فرمت تتر[USDT] عدد خرید/فروش ──────────────────────────────
    (rf'تتر\s*\[?USDT\]?\s*{NUM}\s*خرید', "buy"),
    (rf'تتر\s*\[?USDT\]?\s*{NUM}\s*فروش', "sell"),
    # ── خرید/فروش[USDT] عدد ────────────────────────────────────────
    (rf'خرید\s*\[?USDT\]?\s*{NUM}', "buy"),
    (rf'فروش\s*\[?USDT\]?\s*{NUM}', "sell"),
    # ── قیمت/نرخ تتر : عدد ─────────────────────────────────────────
    (rf'(?:قیمت|نرخ)\s*تتر\s*[:\-]?\s*{NUM}', "buy"),
    # ── نرخ/قیمت تتر عدد تومان (فرمت تترلند) ───────────────────────
    (rf'(?:نرخ|قیمت)\s*تتر\s*[:\-]?\s*{NUM}\s*تومان', "buy"),
    # ── خرید/فروش : عدد ─────────────────────────────────────────────
    (rf'خرید\s*[:\-|]\s*{NUM}', "buy"),
    (rf'فروش\s*[:\-|]\s*{NUM}', "sell"),
    (rf'buy\s*[:\-|]\s*{NUM}', "buy"),
    (rf'sell\s*[:\-|]\s*{NUM}', "sell"),
    # ── قیمت خرید / قیمت فروش ───────────────────────────────────────
    (rf'قیمت\s*خرید[^\d۰-۹٠-٩]{{0,15}}{NUM}', "buy"),
    (rf'قیمت\s*فروش[^\d۰-۹٠-٩]{{0,15}}{NUM}', "sell"),
    # ── نرخ خرید / نرخ فروش ─────────────────────────────────────────
    (rf'نرخ\s*خرید[^\d۰-۹٠-٩]{{0,10}}{NUM}', "buy"),
    (rf'نرخ\s*فروش[^\d۰-۹٠-٩]{{0,10}}{NUM}', "sell"),
    # ── خرید/فروش با فلش یا آیکون ───────────────────────────────────
    (rf'خرید\s*[←→➡⬅🔴🟢✅◈◆◇]?\s*{NUM}', "buy"),
    (rf'فروش\s*[←→➡⬅🔴🟢✅◈◆◇]?\s*{NUM}', "sell"),
    # ── تتر : خرید/فروش عدد ─────────────────────────────────────────
    (rf'تتر\s*[:\-]?\s*خرید\s*[:\-]?\s*{NUM}', "buy"),
    (rf'تتر\s*[:\-]?\s*فروش\s*[:\-]?\s*{NUM}', "sell"),
]

# کلمات کلیدی که نشان می‌دهند پیام درباره تتر/USDT است
_USDT_KEYWORDS = re.compile(r'تتر|USDT|usdt|تدر|تتر', re.IGNORECASE)

# الگوی پشتیبان: هر عدد ۵ تا ۷ رقمی در کنار «تومان» یا در پیام تتری
_FALLBACK_NUM = re.compile(
    r'([\d۰-۹٠-٩]{2,3}[،,٬][\d۰-۹٠-٩]{3}(?:[،,٬][\d۰-۹٠-٩]{3})?)'
    r'(?=\s*تومان|\s*$|\s*\n|\s*[—\-\|])',
    re.MULTILINE
)


def _to_float(raw: str):
    cleaned = raw.translate(FA_DIGITS).replace(",", "").replace("،", "").replace("٬", "").strip()
    try:
        val = float(cleaned)
        return val if 50_000 <= val <= 999_999_999 else None
    except ValueError:
        return None


def extract_prices(text: str):
    prices = {}

    # ۱. الگوهای اصلی
    for pattern, side in PRICE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = _to_float(m.group(1))
            if val and side not in prices:
                prices[side] = val

    # ۲. اگر هنوز قیمتی پیدا نشد و پیام درباره تتر است، هر عدد در محدوده تومان
    if not prices and _USDT_KEYWORDS.search(text):
        for m in _FALLBACK_NUM.finditer(text):
            val = _to_float(m.group(1))
            if val and 50_000 <= val <= 999_999:
                prices.setdefault("buy", val)
                break

    # ۳. اگر هنوز نشد، عدد ۵–۷ رقمی ساده در پیام تتری
    if not prices and _USDT_KEYWORDS.search(text):
        simple = re.findall(
            r'[\d۰-۹٠-٩]{2,3}[،,٬]?[\d۰-۹٠-٩]{3}', text)
        for raw in simple:
            val = _to_float(raw)
            if val and 50_000 <= val <= 999_999:
                prices.setdefault("buy", val)
                break

    return prices


# ── Shamsi (Jalali) Date Conversion ──────────────────────────────────────────
def gregorian_to_jalali(gy, gm, gd):
    g_ym = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    jy = 0 if gy <= 1600 else 979
    gy -= 600 if gy <= 1600 else 1600
    gm -= 1
    g_day = 365*gy + (gy+3)//4 - (gy+99)//100 + (gy+399)//400
    for i in range(gm):
        g_day += g_ym[i]
    if gm > 1 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day += 1
    g_day += gd - 1
    j_day = g_day - 79
    j_np  = j_day // 12053
    j_day %= 12053
    jy   += 979 * j_np
    jy   += 33 * (j_day // 1461)
    j_day %= 1461
    if j_day >= 366:
        jy   += (j_day - 1) // 365
        j_day = (j_day - 1) % 365
    jm_days = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    jm, jd = 12, 29
    for i, v in enumerate(jm_days):
        if j_day < v:
            jm = i + 1
            jd = j_day + 1
            break
        j_day -= v
    return jy, jm, jd


def shamsi_now():
    n  = datetime.now()
    jy, jm, jd = gregorian_to_jalali(n.year, n.month, n.day)
    return f"{jy}/{jm:02d}/{jd:02d}", n.strftime("%H:%M")


# ── Telegram Bot API ──────────────────────────────────────────────────────────
def bot_send_message(token: str, chat_id: str, text: str, buttons_raw: str = "") -> dict:
    keyboard = []
    for line in buttons_raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        row = []
        for part in line.split("||"):
            part = part.strip()
            if "|" in part:
                btn_text, btn_url = part.split("|", 1)
                row.append({"text": btn_text.strip(), "url": btn_url.strip()})
            elif part:
                row.append({"text": part, "callback_data": part})
        if row:
            keyboard.append(row)

    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps({"inline_keyboard": keyboard})

    data = urllib.parse.urlencode(payload).encode("utf-8")
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    req  = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


# ── Telegram Client ───────────────────────────────────────────────────────────
async def fetch_channel_prices(api_id, api_hash, phone, channels, limit,
                                progress_cb, result_cb, error_cb, code_cb, password_cb):
    try:
        from telethon import TelegramClient
        from telethon.errors import FloodWaitError
    except ImportError:
        error_cb("Telethon is not installed. Run: pip install telethon")
        return

    session_file = str(Path(__file__).parent / "chartonex_session")
    client = TelegramClient(session_file, int(api_id), api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.start(phone=phone, code_callback=code_cb, password=password_cb)
    except Exception as e:
        error_cb(f"خطا در اتصال به تلگرام:\n{e}")
        await client.disconnect()
        return

    results = []
    total = len(channels)

    for idx, ch in enumerate(channels):
        url = ch["url"].strip()
        progress_cb(idx, total, f"در حال خواندن: {url}")
        try:
            entity = await client.get_entity(url)
            latest_buy = latest_sell = None
            latest_buy_date = latest_sell_date = ""
            latest_buy_preview = latest_sell_preview = ""

            async for msg in client.iter_messages(entity, limit=int(limit)):
                if msg.text:
                    prices = extract_prices(msg.text)
                    if prices:
                        date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
                        preview = msg.text[:120].replace("\n", " ")
                        if latest_buy is None and prices.get("buy"):
                            latest_buy = prices["buy"]
                            latest_buy_date = date_str
                            latest_buy_preview = preview
                        if latest_sell is None and prices.get("sell"):
                            latest_sell = prices["sell"]
                            latest_sell_date = date_str
                            latest_sell_preview = preview
                        if latest_buy is not None and latest_sell is not None:
                            break

            if latest_buy or latest_sell:
                results.append({
                    "channel": ch.get("name") or url,
                    "url": url,
                    "date": latest_buy_date or latest_sell_date,
                    "buy": latest_buy,
                    "sell": latest_sell,
                    "text_preview": latest_buy_preview or latest_sell_preview,
                })
            else:
                progress_cb(idx, total, f"⚠ هیچ قیمتی در {url} یافت نشد — نمونه پیام‌ها:")
                count = 0
                async for msg in client.iter_messages(entity, limit=5):
                    if msg.text and count < 3:
                        progress_cb(idx, total, f"  ▶ {msg.text[:300].replace(chr(10), ' | ')}")
                        count += 1
        except FloodWaitError as e:
            error_cb(f"Flood wait: {e.seconds} ثانیه صبر کنید")
            break
        except Exception as e:
            results.append({
                "channel": url, "url": url,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "buy": None, "sell": None,
                "text_preview": f"خطا: {e}",
            })

    await client.disconnect()
    progress_cb(total, total, "اتمام")
    result_cb(results)


# ══════════════════════════════════════════════════════════════════════════════
# GUI
# ══════════════════════════════════════════════════════════════════════════════

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEADER = ("Segoe UI", 15, "bold")
FONT_BODY   = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 11)
FONT_PRICE  = ("Segoe UI", 28, "bold")
FONT_NAV    = ("Segoe UI", 13)


def _f(size, bold=False):
    return ctk.CTkFont("Segoe UI", size, "bold" if bold else "normal")


class ChartoneXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ChartoneX  |  نرخ لحظه‌ای تتر")
        self.geometry("1260x760")
        self.minsize(1000, 660)
        self.configure(fg_color=C["bg"])

        self.channels = load_channels()
        self.settings = load_settings()
        self.results  = []
        self._running = False
        self._stop_flag = threading.Event()
        self._next_run_after_id = None

        self._build_ui()
        self._refresh_channel_list()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top accent stripe — gradient-like via two stacked thin frames
        top_bar = ctk.CTkFrame(self, height=3, fg_color=C["blue"], corner_radius=0)
        top_bar.pack(side="top", fill="x")

        # RTL: sidebar on right, content on left
        self.main_area = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=C["sidebar"], corner_radius=0)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar separator
        ctk.CTkFrame(self.sidebar, width=1, fg_color=C["border"], corner_radius=0).pack(
            side="left", fill="y")

        self._build_sidebar()

        self.pages = {}
        self._content = ctk.CTkFrame(self.main_area, fg_color=C["bg"], corner_radius=0)
        self._content.pack(fill="both", expand=True)

        self._build_output_page()
        self._build_channels_page()
        self._build_scrape_page()
        self._build_calc_page()
        self._build_format_page()
        self._build_settings_page()

        self._show_page("output")
        self._bind_paste_everywhere()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        # ── Logo block ────────────────────────────────────────────────────────
        logo_wrap = ctk.CTkFrame(self.sidebar, fg_color=C["bg2"], corner_radius=0)
        logo_wrap.pack(fill="x")

        logo = ctk.CTkFrame(logo_wrap, fg_color="transparent")
        logo.pack(fill="x", padx=20, pady=(24, 20))

        # Icon badge
        badge = ctk.CTkFrame(logo, fg_color=C["blue_dim"],
                              corner_radius=10, border_width=1,
                              border_color=C["blue_glow"])
        badge.pack(anchor="e", pady=(0, 10))
        ctk.CTkLabel(badge, text="  ◈  ChartoneX  ",
                     font=_f(16, True), text_color=C["blue"]).pack(
            padx=4, pady=6)

        ctk.CTkLabel(logo, text="نرخ لحظه‌ای تتر از تلگرام",
                     font=_f(10), text_color=C["text3"],
                     anchor="e").pack(fill="x")

        ctk.CTkFrame(logo_wrap, height=1, fg_color=C["border"], corner_radius=0).pack(fill="x")

        # ── Navigation ────────────────────────────────────────────────────────
        # Section label
        ctk.CTkLabel(self.sidebar, text="  منوی اصلی",
                     font=_f(9), text_color=C["text3"],
                     anchor="e").pack(fill="x", padx=16, pady=(14, 4))

        nav_items = [
            ("📊", "خروجی",        "output"),
            ("📡", "کانال‌ها",     "channels"),
            ("🔍", "استخراج",      "scrape"),
            ("🧮", "محاسبه قیمت", "calc"),
            ("📤", "فرمت خروجی",  "format"),
            ("⚙️", "تنظیمات",     "settings"),
        ]
        self._nav_btns = {}
        self._nav_indicators = {}

        for icon, label, key in nav_items:
            wrapper = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=50)
            wrapper.pack(fill="x", padx=8, pady=2)
            wrapper.pack_propagate(False)

            # Right-side glow indicator
            indicator = ctk.CTkFrame(wrapper, width=4, fg_color="transparent",
                                     corner_radius=2)
            indicator.pack(side="right", fill="y")
            self._nav_indicators[key] = indicator

            btn = ctk.CTkButton(
                wrapper,
                text=f"{label}    {icon}",
                anchor="e",
                height=50,
                corner_radius=8,
                fg_color="transparent",
                hover_color=C["sidebar_hov"],
                text_color=C["text2"],
                font=_f(13),
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(fill="both", expand=True)
            self._nav_btns[key] = btn

        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"]).pack(
            fill="x", padx=8, pady=(14, 0))

        # ── Bottom status ─────────────────────────────────────────────────────
        self._conn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._conn_frame.pack(side="bottom", fill="x", padx=14, pady=(0, 18))

        status_row = ctk.CTkFrame(self._conn_frame, fg_color=C["buy_dim"],
                                  corner_radius=10, border_width=1,
                                  border_color=C["buy_glow"])
        status_row.pack(fill="x")

        ctk.CTkFrame(status_row, width=8, height=8,
                     fg_color=C["buy"], corner_radius=4).pack(
            side="left", padx=(12, 6), pady=12)

        ctk.CTkLabel(status_row, text="آماده به کار",
                     font=_f(10), text_color=C["buy"],
                     anchor="e").pack(side="right", padx=12, pady=12)

        ctk.CTkLabel(self._conn_frame, text="ChartoneX v2.1",
                     font=_f(9), text_color=C["text3"],
                     anchor="center").pack(pady=(8, 0))

    def _show_page(self, key: str):
        for k, f in self.pages.items():
            f.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color=C["blue_dim"], text_color=C["blue"],
                              font=_f(13, True),
                              border_width=1, border_color=C["blue_glow"])
                self._nav_indicators[k].configure(fg_color=C["blue"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text2"],
                              font=_f(13, False),
                              border_width=0)
                self._nav_indicators[k].configure(fg_color="transparent")

    # ── Paste helpers ─────────────────────────────────────────────────────────
    def _bind_paste_everywhere(self):
        def walk(w):
            if isinstance(w, ctk.CTkEntry):
                inn = w._entry
                inn.bind("<Control-v>", lambda e, i=inn: self._paste(i))
                inn.bind("<Control-V>", lambda e, i=inn: self._paste(i))
                inn.bind("<Button-3>",  lambda e, i=inn: self._ctx_entry(e, i))
            elif isinstance(w, ctk.CTkTextbox):
                inn = w._textbox
                inn.bind("<Control-v>", lambda e, i=inn: self._paste_tb(i))
                inn.bind("<Control-V>", lambda e, i=inn: self._paste_tb(i))
                inn.bind("<Button-3>",  lambda e, i=inn: self._ctx_entry(e, i))
            for ch in w.winfo_children():
                walk(ch)
        walk(self)

    def _paste(self, w):
        try: w.insert(tk.INSERT, self.clipboard_get())
        except Exception: pass
        return "break"

    def _paste_tb(self, w):
        try: w.insert(tk.INSERT, self.clipboard_get())
        except Exception: pass
        return "break"

    def _ctx_entry(self, event, w):
        m = tk.Menu(self, tearoff=0, bg=C["card"], fg=C["text"],
                    activebackground=C["blue"], activeforeground="#000",
                    font=("Segoe UI", 11))
        m.add_command(label="پیست",       command=lambda: self._paste(w))
        m.add_command(label="انتخاب همه", command=lambda: w.select_range(0, "end")
                      if hasattr(w, "select_range") else None)
        m.tk_popup(event.x_root, event.y_root)

    # ── Shared widget factory ─────────────────────────────────────────────────
    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=C["card"],
                            corner_radius=14, border_width=1,
                            border_color=C["border"], **kw)

    def _label(self, parent, text, size=12, bold=False,
               color=None, anchor="e", **kw):
        return ctk.CTkLabel(parent, text=text,
                            font=_f(size, bold),
                            text_color=color or C["text"],
                            anchor=anchor, **kw)

    def _entry(self, parent, placeholder="", secret=False, value=""):
        e = ctk.CTkEntry(parent, placeholder_text=placeholder,
                         height=42, fg_color=C["input"],
                         border_color=C["border2"],
                         border_width=1,
                         text_color=C["text"],
                         font=_f(12),
                         justify="right",
                         show="*" if secret else "")
        if value:
            e.insert(0, value)
        return e

    def _btn(self, parent, text, cmd, primary=True, w=None, h=38):
        kw = dict(height=h, corner_radius=8, font=_f(12, True),
                  command=cmd, text=text)
        if w:
            kw["width"] = w
        if primary:
            kw.update(fg_color=C["blue"], hover_color=C["blue_hov"],
                      text_color="#ffffff")
        else:
            kw.update(fg_color=C["card2"], hover_color=C["input"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text2"])
        return ctk.CTkButton(parent, **kw)

    def _page_header(self, page, title, subtitle=""):
        bar = ctk.CTkFrame(page, fg_color=C["bg2"], corner_radius=0, height=72)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkFrame(bar, height=1, fg_color=C["border"], corner_radius=0).pack(
            side="bottom", fill="x")

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30)

        # Right-side decorative bracket + title
        txt_block = ctk.CTkFrame(inner, fg_color="transparent")
        txt_block.pack(side="right", fill="y")

        title_row = ctk.CTkFrame(txt_block, fg_color="transparent")
        title_row.pack(anchor="e", pady=(18, 2))

        self._label(title_row, title, 19, True, anchor="e").pack(side="right")
        ctk.CTkFrame(title_row, width=4, height=22,
                     fg_color=C["blue"], corner_radius=2).pack(
            side="right", padx=(0, 10))

        if subtitle:
            self._label(txt_block, subtitle, 10, color=C["text3"],
                        anchor="e").pack(anchor="e")

        return bar

    # ══════════════════════════════════════════════════════════════════════════
    # OUTPUT PAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_output_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["output"] = page

        self._page_header(page, "خروجی قیمت‌ها", "آخرین قیمت‌های استخراج‌شده از کانال‌ها")

        # ─ Summary bar ───────────────────────────────────────────────────────
        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(16, 8))

        self._best_buy_card  = self._make_summary_card(bar, "بهترین خرید", "—", C["buy"])
        self._best_sell_card = self._make_summary_card(bar, "بهترین فروش", "—", C["sell"])
        self._total_card     = self._make_summary_card(bar, "تعداد کانال‌ها", "0", C["blue"])
        self._time_card      = self._make_summary_card(bar, "آخرین بروزرسانی", "—", C["gold"])

        self._best_buy_card.pack(side="right", fill="x", expand=True, padx=(4, 0))
        self._best_sell_card.pack(side="right", fill="x", expand=True, padx=4)
        self._total_card.pack(side="right", fill="x", expand=True, padx=4)
        self._time_card.pack(side="right", fill="x", expand=True, padx=(0, 4))

        # ─ Channel cards grid ────────────────────────────────────────────────
        self._out_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self._out_scroll.pack(fill="both", expand=True, padx=24, pady=(4, 8))

        # ─ Bottom bar ────────────────────────────────────────────────────────
        bot = ctk.CTkFrame(page, fg_color="transparent")
        bot.pack(fill="x", padx=24, pady=(0, 16))
        self._btn(bot, "💾  ذخیره CSV", self._export_csv, primary=False, h=36).pack(side="right")

    def _make_summary_card(self, parent, label, value, color):
        color_to_dim = {
            C["buy"]:  C["buy_dim"],
            C["sell"]: C["sell_dim"],
            C["blue"]: C["blue_dim"],
            C["gold"]: C["gold_dim"],
        }
        color_to_border = {
            C["buy"]:  C["buy_glow"],
            C["sell"]: C["sell_glow"],
            C["blue"]: C["blue_glow"],
            C["gold"]: C["gold_glow"],
        }
        bg  = color_to_dim.get(color, C["card"])
        brd = color_to_border.get(color, C["border"])
        outer = ctk.CTkFrame(parent, fg_color=bg, corner_radius=14,
                             border_width=1, border_color=brd)
        ctk.CTkFrame(outer, height=4, fg_color=color, corner_radius=0).pack(fill="x")
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=(12, 16))
        self._label(inner, label, 9, color=C["text3"]).pack(anchor="e", fill="x")
        val_lbl = self._label(inner, value, 22, True, color=color)
        val_lbl.pack(anchor="e", fill="x", pady=(6, 0))
        outer._val = val_lbl
        return outer

    def _refresh_output(self):
        for w in self._out_scroll.winfo_children():
            w.destroy()

        buys  = [r["buy"]  for r in self.results if r.get("buy")]
        sells = [r["sell"] for r in self.results if r.get("sell")]

        self._best_buy_card._val.configure(
            text=f"{max(buys):,.0f}" if buys else "—")
        self._best_sell_card._val.configure(
            text=f"{min(sells):,.0f}" if sells else "—")
        self._total_card._val.configure(text=str(len(self.results)))
        self._time_card._val.configure(
            text=datetime.now().strftime("%H:%M:%S"))

        if not self.results:
            self._label(self._out_scroll,
                        "هنوز داده‌ای استخراج نشده — برو به صفحه استخراج",
                        13, color=C["text3"]).pack(pady=60)
            return

        # میانگین قیمت کانال‌های تک‌نرخی
        single_prices = []
        for r in self.results:
            has_buy  = bool(r.get("buy"))
            has_sell = bool(r.get("sell"))
            if has_buy != has_sell:  # فقط یکی از دو قیمت موجود است
                single_prices.append(r.get("buy") or r.get("sell"))
        avg_single = (sum(single_prices) / len(single_prices)) if single_prices else None

        # Two-column grid
        grid = ctk.CTkFrame(self._out_scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, r in enumerate(self.results):
            col = i % 2
            row = i // 2
            self._channel_price_card(grid, r, row, col, avg_single)

    def _channel_price_card(self, grid, r, row, col, avg_single=None):
        has_buy  = bool(r.get("buy"))
        has_sell = bool(r.get("sell"))
        is_single = has_buy != has_sell

        top_color   = C["gold"]  if is_single else C["blue"]
        card_border = C["gold_glow"] if is_single else C["border"]

        card = ctk.CTkFrame(grid, fg_color=C["card"], corner_radius=14,
                            border_width=1, border_color=card_border)
        card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")

        # ── Top colored accent (4px) ──────────────────────────────────────────
        ctk.CTkFrame(card, height=4, fg_color=top_color, corner_radius=0).pack(fill="x")

        # ── Channel header ────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(card, fg_color=C["card2"],
                           corner_radius=0, border_width=0)
        hdr.pack(fill="x", padx=0, pady=(0, 0))

        # Channel name on right
        name_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        name_frame.pack(side="right", padx=14, pady=10)
        self._label(name_frame, r.get("channel", "")[:30], 13, True).pack(anchor="e")
        self._label(name_frame, r.get("date", ""), 9, color=C["text3"]).pack(anchor="e")

        # Badge on left
        if is_single:
            badge = ctk.CTkFrame(hdr, fg_color=C["gold_dim"],
                                 corner_radius=6, border_width=1,
                                 border_color=C["gold"])
            badge.pack(side="left", padx=10, pady=10)
            self._label(badge, "تک‌نرخی", 9, color=C["gold"]).pack(padx=8, pady=4)

        # Separator
        ctk.CTkFrame(card, height=1, fg_color=C["border"], corner_radius=0).pack(fill="x")

        # ── Price boxes ───────────────────────────────────────────────────────
        prices_row = ctk.CTkFrame(card, fg_color="transparent")
        prices_row.pack(fill="x", padx=10, pady=10)

        if is_single:
            single_val = r.get("buy") or r.get("sell")
            avg_box = ctk.CTkFrame(prices_row, fg_color=C["gold_dim"],
                                   corner_radius=10, border_width=1,
                                   border_color=C["gold"])
            avg_box.pack(fill="both", expand=True)
            self._label(avg_box, "میانگین قیمت", 10, color=C["gold"]).pack(
                anchor="e", padx=18, pady=(16, 0))
            self._label(avg_box, f"{single_val:,.0f}", 28, True,
                        color=C["gold"]).pack(anchor="e", padx=18, pady=(4, 16))

        else:
            # فروش (چپ)
            sell_box = ctk.CTkFrame(prices_row, fg_color=C["sell_dim"],
                                    corner_radius=10, border_width=1,
                                    border_color=C["sell_glow"])
            sell_box.pack(side="left", fill="both", expand=True, padx=(0, 5))
            ctk.CTkFrame(sell_box, height=2, fg_color=C["sell"],
                         corner_radius=0).pack(fill="x")
            self._label(sell_box, "▾  فروش", 10, color=C["sell"]).pack(
                anchor="e", padx=14, pady=(12, 0))
            sell_val = f"{r['sell']:,.0f}" if has_sell else "—"
            self._label(sell_box, sell_val, 24, True, color=C["sell"]).pack(
                anchor="e", padx=14, pady=(4, 12))

            # خرید (راست)
            buy_box = ctk.CTkFrame(prices_row, fg_color=C["buy_dim"],
                                   corner_radius=10, border_width=1,
                                   border_color=C["buy_glow"])
            buy_box.pack(side="right", fill="both", expand=True, padx=(5, 0))
            ctk.CTkFrame(buy_box, height=2, fg_color=C["buy"],
                         corner_radius=0).pack(fill="x")
            self._label(buy_box, "▴  خرید", 10, color=C["buy"]).pack(
                anchor="e", padx=14, pady=(12, 0))
            buy_val = f"{r['buy']:,.0f}" if has_buy else "—"
            self._label(buy_box, buy_val, 24, True, color=C["buy"]).pack(
                anchor="e", padx=14, pady=(4, 12))

    def _export_csv(self):
        if not self.results:
            messagebox.showinfo("خروجی خالی", "ابتدا استخراج را اجرا کنید.")
            return
        filename = f"prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        lines = ["channel,buy,sell,date,preview"]
        for r in self.results:
            preview = r.get("text_preview", "").replace(",", "،")
            lines.append(
                f"{r.get('channel','')},{r.get('buy','')},{r.get('sell','')}"
                f",{r.get('date','')},{preview}")
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("ذخیره شد", f"فایل ذخیره شد:\n{filename}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHANNELS PAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_channels_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["channels"] = page
        self._page_header(page, "مدیریت کانال‌ها", "افزودن و مشاهده کانال‌های تلگرام")

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ─ Add form (right column, RTL) ───────────────────────────────────────
        form_card = self._card(body)
        form_card.grid(row=0, column=1, padx=(6, 0), pady=0, sticky="nsew")

        self._label(form_card, "افزودن کانال جدید", 13, True).pack(
            anchor="e", padx=16, pady=(16, 12))

        def _field(label, placeholder, ref_attr, secret=False):
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            self._label(row, label, 11, color=C["text2"]).pack(
                anchor="e", fill="x", pady=(0, 2))
            e = self._entry(row, placeholder, secret)
            e.pack(fill="x")
            setattr(self, ref_attr, e)

        _field("نام کانال", "مثال: صرافی آلفا", "ch_name_entry")
        _field("لینک کانال", "@channel یا https://t.me/channel", "ch_url_entry")

        # Sample textbox
        self._label(form_card, "نمونه پیام کانال", 11, color=C["text2"]).pack(
            anchor="e", padx=16, pady=(8, 2))
        self.ch_sample = ctk.CTkTextbox(
            form_card, height=72,
            fg_color=C["input"], border_color=C["border2"],
            border_width=1, text_color=C["text"],
            font=_f(11))
        self.ch_sample.pack(fill="x", padx=16)

        self.ch_test_lbl = self._label(
            form_card, "یک نمونه پیام paste کنید", 10, color=C["text3"])
        self.ch_test_lbl.pack(anchor="e", padx=16, pady=(4, 0))

        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(10, 16))
        self._btn(btn_row, "+ افزودن", self._add_channel, primary=True, h=36).pack(
            side="right", padx=(6, 0))
        self._btn(btn_row, "🔍 تست", self._test_sample, primary=False, h=36).pack(
            side="right")

        # ─ Channel list (left column) ─────────────────────────────────────────
        list_card = self._card(body)
        list_card.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="nsew")

        list_hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        list_hdr.pack(fill="x", padx=16, pady=(14, 8))
        self._label(list_hdr, "کانال‌های ذخیره‌شده", 12, True).pack(side="right")
        self.ch_count_lbl = self._label(list_hdr, "0 کانال", 10, color=C["text3"])
        self.ch_count_lbl.pack(side="left")

        ctk.CTkFrame(list_card, height=1, fg_color=C["border"]).pack(fill="x", padx=12)

        self._ch_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._ch_scroll.pack(fill="both", expand=True, padx=8, pady=8)

    def _test_sample(self):
        sample = self.ch_sample.get("1.0", "end").strip()
        if not sample:
            self.ch_test_lbl.configure(text="⚠ ابتدا یک نمونه پیام paste کنید",
                                       text_color=C["gold"])
            return
        prices = extract_prices(sample)
        if prices:
            parts = []
            if "buy"  in prices: parts.append(f"خرید: {prices['buy']:,.0f}")
            if "sell" in prices: parts.append(f"فروش: {prices['sell']:,.0f}")
            self.ch_test_lbl.configure(
                text="✓ " + "  |  ".join(parts), text_color=C["buy"])
        else:
            self.ch_test_lbl.configure(
                text="✗ قیمتی یافت نشد", text_color=C["sell"])

    def _add_channel(self):
        name   = self.ch_name_entry.get().strip()
        url    = self.ch_url_entry.get().strip()
        sample = self.ch_sample.get("1.0", "end").strip()
        if not url:
            messagebox.showwarning("ورودی ناقص", "لینک کانال را وارد کنید.")
            return
        if not url.startswith("@") and "t.me/" not in url and not url.startswith("https://"):
            url = "@" + url
        for ch in self.channels:
            if ch["url"] == url:
                messagebox.showinfo("تکراری", "این کانال قبلاً اضافه شده.")
                return
        self.channels.append({
            "name": name or url, "url": url,
            "sample": sample,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        save_channels(self.channels)
        self.ch_name_entry.delete(0, "end")
        self.ch_url_entry.delete(0, "end")
        self.ch_sample.delete("1.0", "end")
        self.ch_test_lbl.configure(text="یک نمونه پیام paste کنید",
                                   text_color=C["text3"])
        self._refresh_channel_list()

    def _refresh_channel_list(self):
        for w in self._ch_scroll.winfo_children():
            w.destroy()
        for idx, ch in enumerate(self.channels):
            self._build_ch_row(idx, ch)
        self.ch_count_lbl.configure(text=f"{len(self.channels)} کانال")

    def _build_ch_row(self, idx, ch):
        sample = ch.get("sample", "")
        prices = extract_prices(sample) if sample else {}
        has_prices = bool(prices)

        if sample:
            badge_txt   = "✓ شناسایی شد" if has_prices else "✗ ناشناخته"
            badge_color = C["buy"] if has_prices else C["sell"]
            left_border = C["buy"] if has_prices else C["sell"]
        else:
            badge_txt, badge_color = "⚠ بدون نمونه", C["gold"]
            left_border = C["gold"]

        # Row card
        row = ctk.CTkFrame(self._ch_scroll, fg_color=C["card"],
                           corner_radius=10, border_width=1,
                           border_color=C["border"])
        row.pack(fill="x", pady=4)

        # Accent left stripe
        ctk.CTkFrame(row, width=3, fg_color=left_border,
                     corner_radius=0).pack(side="left", fill="y")

        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(fill="both", expand=True)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 4))

        # Delete button
        ctk.CTkButton(top, text="✕", width=28, height=28,
                      corner_radius=6, fg_color=C["input"],
                      hover_color=C["sell_dim"], text_color=C["text3"],
                      border_width=1, border_color=C["border2"],
                      font=_f(11),
                      command=lambda i=idx: self._remove_channel(i)).pack(side="left")

        # Badge pill
        badge_bg = C["buy_dim"] if has_prices else (C["sell_dim"] if sample else C["gold_dim"])
        badge_frame = ctk.CTkFrame(top, fg_color=badge_bg,
                                   corner_radius=5, border_width=1,
                                   border_color=badge_color)
        badge_frame.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(badge_frame, text=badge_txt,
                     font=_f(9), text_color=badge_color).pack(padx=7, pady=3)

        # Channel name (right side)
        self._label(top, ch.get("name", ch["url"]), 12, True).pack(side="right")

        self._label(content, ch["url"], 10, color=C["text3"]).pack(
            anchor="e", padx=10, pady=(0, 6))

        if sample:
            prev = ctk.CTkFrame(content, fg_color=C["input"], corner_radius=6)
            prev.pack(fill="x", padx=10, pady=(0, 10))
            self._label(prev, sample[:100].replace("\n", " ↵ "),
                        9, color=C["text3"]).pack(anchor="e", padx=8, pady=5)

    def _remove_channel(self, idx):
        ch = self.channels[idx]
        if messagebox.askyesno("حذف", f"حذف «{ch.get('name', ch['url'])}»؟"):
            self.channels.pop(idx)
            save_channels(self.channels)
            self._refresh_channel_list()

    # ══════════════════════════════════════════════════════════════════════════
    # SCRAPE PAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_scrape_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["scrape"] = page
        self._page_header(page, "استخراج قیمت‌ها", "شروع و مدیریت استخراج خودکار")

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # ─ Interval selector ─────────────────────────────────────────────────
        int_card = self._card(body)
        int_card.pack(fill="x", pady=(0, 12))

        self._label(int_card, "بازه تکرار", 12, True).pack(
            anchor="e", padx=16, pady=(14, 8))

        self._interval_seconds = int(self.settings.get("interval", 60))
        presets = [("۳۰ ثانیه", 30), ("۱ دقیقه", 60), ("۵ دقیقه", 300),
                   ("۱۵ دقیقه", 900), ("۳۰ دقیقه", 1800), ("۱ ساعت", 3600)]
        self._preset_btns = {}
        prow = ctk.CTkFrame(int_card, fg_color="transparent")
        prow.pack(fill="x", padx=16, pady=(0, 14))

        for lbl, secs in presets:
            active = secs == self._interval_seconds
            btn = ctk.CTkButton(
                prow, text=lbl, width=90, height=32, corner_radius=8,
                fg_color=C["blue"] if active else C["input"],
                hover_color=C["blue_hov"],
                text_color="#fff",
                font=_f(11),
                command=lambda s=secs: self._set_interval(s),
            )
            btn.pack(side="right", padx=3)
            self._preset_btns[secs] = btn

        # ─ Progress + status ─────────────────────────────────────────────────
        prog_card = self._card(body)
        prog_card.pack(fill="x", pady=(0, 12))

        self._prog_bar = ctk.CTkProgressBar(
            prog_card, height=10, progress_color=C["blue"],
            fg_color=C["border"], corner_radius=5)
        self._prog_bar.pack(fill="x", padx=16, pady=(14, 8))
        self._prog_bar.set(0)

        pstatus = ctk.CTkFrame(prog_card, fg_color="transparent")
        pstatus.pack(fill="x", padx=16, pady=(0, 12))
        self._status_lbl = self._label(pstatus, "آماده", 11, color=C["text2"])
        self._status_lbl.pack(side="right")
        self._countdown_lbl = self._label(pstatus, "", 11, True, color=C["gold"])
        self._countdown_lbl.pack(side="left")

        # ─ Control buttons ───────────────────────────────────────────────────
        btn_card = ctk.CTkFrame(body, fg_color="transparent")
        btn_card.pack(fill="x", pady=(0, 12))

        self._stop_btn = ctk.CTkButton(
            btn_card, text="⏹  توقف", height=50, corner_radius=8,
            fg_color=C["sell_dim"], hover_color=C["sell_glow"],
            border_width=1, border_color=C["sell_glow"],
            text_color=C["sell"], font=_f(13, True),
            state="disabled", command=self._stop_scraping)
        self._stop_btn.pack(side="right", padx=(6, 0))

        self._start_btn = ctk.CTkButton(
            btn_card, text="▶  شروع استخراج", height=50, corner_radius=8,
            fg_color=C["teal"], hover_color=C["teal_hov"],
            text_color="#fff", font=_f(14, True),
            command=self._start_scraping)
        self._start_btn.pack(side="right")

        self._btn(btn_card, "📊 مشاهده خروجی",
                  lambda: self._show_page("output"),
                  primary=False, h=46).pack(side="left")

        # ─ Log ───────────────────────────────────────────────────────────────
        log_card = self._card(body)
        log_card.pack(fill="both", expand=True)

        log_hdr = ctk.CTkFrame(log_card, fg_color="transparent")
        log_hdr.pack(fill="x", padx=16, pady=(12, 4))
        self._label(log_hdr, "گزارش عملیات", 12, True).pack(side="right")
        self._btn(log_hdr, "📋 کپی", self._copy_log,
                  primary=False, w=80, h=26).pack(side="left")

        self._log_box = ctk.CTkTextbox(
            log_card, fg_color=C["input"], text_color=C["text2"],
            font=_f(10), corner_radius=8, border_width=0)
        self._log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        inn = self._log_box._textbox
        inn.bind("<Control-c>", lambda e: self._copy_sel_log(inn))
        inn.bind("<Control-C>", lambda e: self._copy_sel_log(inn))
        inn.bind("<Control-a>", lambda e: self._sel_all_log())
        inn.bind("<Control-A>", lambda e: self._sel_all_log())
        inn.bind("<Button-3>",  self._log_ctx)
        self._log_box.configure(state="disabled")

    def _set_interval(self, secs):
        self._interval_seconds = secs
        self.settings["interval"] = secs
        save_settings(self.settings)
        for s, btn in self._preset_btns.items():
            btn.configure(fg_color=C["blue"] if s == secs else C["input"])

    def _fmt_interval(self, secs):
        if secs < 60: return f"{secs} ثانیه"
        if secs < 3600: return f"{secs // 60} دقیقه"
        return f"{secs // 3600} ساعت"

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}]  {msg}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _copy_log(self):
        content = self._log_box._textbox.get("1.0", "end").strip()
        if content:
            self.clipboard_clear(); self.clipboard_append(content)

    def _copy_sel_log(self, w):
        try:
            sel = w.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear(); self.clipboard_append(sel)
        except tk.TclError: pass
        return "break"

    def _sel_all_log(self):
        self._log_box._textbox.tag_add(tk.SEL, "1.0", "end")
        return "break"

    def _log_ctx(self, event):
        m = tk.Menu(self, tearoff=0, bg=C["card"], fg=C["text"],
                    activebackground=C["blue"], activeforeground="#000",
                    font=("Segoe UI", 11))
        m.add_command(label="کپی انتخاب‌شده",
                      command=lambda: self._copy_sel_log(self._log_box._textbox))
        m.add_command(label="انتخاب همه", command=self._sel_all_log)
        m.add_command(label="کپی همه",    command=self._copy_log)
        m.tk_popup(event.x_root, event.y_root)

    def _start_scraping(self):
        if not self.channels:
            messagebox.showwarning("بدون کانال", "ابتدا کانال‌هایی اضافه کنید.")
            return
        s = self.settings
        if not s.get("api_id") or not s.get("api_hash") or not s.get("phone"):
            messagebox.showwarning("تنظیمات ناقص",
                                   "API ID، API Hash و شماره تلفن را در تنظیمات وارد کنید.")
            self._show_page("settings")
            return
        self._running = True
        self._stop_flag.clear()
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._run_once()

    def _stop_scraping(self):
        self._running = False
        self._stop_flag.set()
        if self._next_run_after_id:
            self.after_cancel(self._next_run_after_id)
            self._next_run_after_id = None
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._countdown_lbl.configure(text="")
        self._status_lbl.configure(text="متوقف شد")
        self._log("⏹ استخراج متوقف شد.")

    def _run_once(self):
        if not self._running: return
        s = self.settings
        self._prog_bar.set(0)
        self._countdown_lbl.configure(text="")
        self._log(f"── شروع دور جدید از {len(self.channels)} کانال ──")

        def pcb(done, total, msg):
            self.after(0, lambda: self._on_progress(done, total, msg))
        def rcb(results):
            self.after(0, lambda: self._on_results(results))
        def ecb(msg):
            self.after(0, lambda: self._on_error(msg))
        def code_cb():
            return self._ask_input("کد تأیید تلگرام",
                                   "کد ارسال‌شده از تلگرام را وارد کنید:")
        def pass_cb():
            return self._ask_input("رمز دو مرحله‌ای",
                                   "رمز ورود دو مرحله‌ای را وارد کنید:", secret=True)

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(fetch_channel_prices(
                s["api_id"], s["api_hash"], s["phone"],
                self.channels, 20,
                pcb, rcb, ecb, code_cb, pass_cb))
            loop.close()

        threading.Thread(target=run, daemon=True).start()

    def _on_progress(self, done, total, msg):
        self._prog_bar.set(done / total if total else 0)
        self._status_lbl.configure(text=msg)
        self._log(msg)

    def _on_results(self, results):
        self.results = results
        self._log(f"✓ {len(results)} کانال پردازش شد.")
        self._refresh_output()
        self._show_page("output")
        if self._running:
            self._countdown(self._interval_seconds)

    def _countdown(self, remaining):
        if not self._running: return
        if remaining <= 0:
            self._countdown_lbl.configure(text="")
            self._run_once()
            return
        m, s = divmod(remaining, 60)
        txt = f"دور بعدی: {m:02d}:{s:02d}" if m else f"دور بعدی: {s} ثانیه"
        self._countdown_lbl.configure(text=txt)
        self._next_run_after_id = self.after(
            1000, lambda: self._countdown(remaining - 1))

    def _on_error(self, msg):
        self._start_btn.configure(state="normal")
        self._log(f"✗ خطا: {msg}")
        messagebox.showerror("خطا", msg)

    def _ask_input(self, title, prompt, secret=False):
        holder = [None]
        ev = threading.Event()

        def show():
            dlg = ctk.CTkToplevel(self)
            dlg.title(title)
            dlg.geometry("380x210")
            dlg.resizable(False, False)
            dlg.configure(fg_color=C["card"])
            dlg.grab_set(); dlg.lift(); dlg.focus_force()

            self._label(dlg, prompt, 12, color=C["text"]).pack(
                padx=24, pady=(24, 10))
            e = self._entry(dlg, secret=secret)
            e.pack(padx=24, fill="x", pady=(0, 16))
            e.focus()

            def confirm(ev=None):
                holder[0] = e.get().strip()
                dlg.destroy(); ev.set() if hasattr(ev, 'set') else None

            def ok(ev_arg=None):
                holder[0] = e.get().strip()
                dlg.destroy()
                ev.set()

            e.bind("<Return>", ok)
            self._btn(dlg, "تأیید", ok, primary=True, w=120, h=36).pack()
            dlg.protocol("WM_DELETE_WINDOW", ok)

        self.after(0, show)
        ev.wait(timeout=120)
        return holder[0] or ""

    # ══════════════════════════════════════════════════════════════════════════
    # CALC PAGE — محاسبه قیمت کانال مقصد
    # ══════════════════════════════════════════════════════════════════════════
    def _build_calc_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["calc"] = page
        self._page_header(page, "محاسبه قیمت کانال مقصد",
                          "مقایسه دو کانال و محاسبه قیمت پیشنهادی")

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ─ فرم (ستون راست) ───────────────────────────────────────────────────
        form = self._card(body)
        form.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        self._label(form, "پارامترهای محاسبه", 13, True).pack(
            anchor="e", padx=16, pady=(16, 12))

        ch_names = [ch.get("name", ch["url"]) for ch in self.channels] or ["— کانالی ندارید —"]

        def _dropdown(lbl_text, attr, default_key):
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=5)
            self._label(row, lbl_text, 11, color=C["text2"]).pack(anchor="e", fill="x", pady=(0, 3))
            saved = self.settings.get(default_key, "")
            val = saved if saved in ch_names else ch_names[0]
            var = tk.StringVar(value=val)
            opt = ctk.CTkOptionMenu(row, variable=var, values=ch_names,
                                    fg_color=C["input"], button_color=C["blue"],
                                    button_hover_color=C["blue_hov"],
                                    text_color=C["text"], font=_f(12),
                                    dropdown_fg_color=C["card"],
                                    dropdown_text_color=C["text"])
            opt.pack(fill="x")
            setattr(self, attr, var)
            return var

        self._calc_src_var = _dropdown("کانال مبدا", "_calc_src_var", "calc_source")
        self._calc_dst_var = _dropdown("کانال مقصد", "_calc_dst_var", "calc_dest")

        def _num_field(lbl_text, attr, default_key):
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=5)
            self._label(row, lbl_text, 11, color=C["text2"]).pack(anchor="e", fill="x", pady=(0, 3))
            e = self._entry(row, "عدد به تومان",
                            value=str(self.settings.get(default_key, "")))
            e.pack(fill="x")
            setattr(self, attr, e)

        _num_field("آستانه اختلاف (تومان)", "_calc_threshold_e", "calc_threshold")
        _num_field("کسر از میانگین (تومان)", "_calc_deduction_e", "calc_deduction")

        ctk.CTkFrame(form, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=10)

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        self._btn(btn_row, "🧮 محاسبه", self._do_calc, primary=True, h=40).pack(
            side="right", padx=(6, 0))
        self._btn(btn_row, "💾 ذخیره تنظیمات", self._save_calc_settings,
                  primary=False, h=40).pack(side="right")

        # ─ نتیجه (ستون چپ) ───────────────────────────────────────────────────
        result_col = self._card(body)
        result_col.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        self._label(result_col, "نتیجه محاسبه", 13, True).pack(
            anchor="e", padx=16, pady=(16, 12))

        ctk.CTkFrame(result_col, height=1, fg_color=C["border"]).pack(fill="x", padx=12)

        # کارت‌های نتیجه
        stats = ctk.CTkFrame(result_col, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=12)
        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)

        def _stat_box(parent, label, attr, color, r, c):
            box = ctk.CTkFrame(parent, fg_color=C["input"], corner_radius=10,
                               border_width=1, border_color=C["border2"])
            box.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            self._label(box, label, 9, color=C["text3"]).pack(anchor="e", padx=10, pady=(8, 0))
            lbl = self._label(box, "—", 16, True, color=color)
            lbl.pack(anchor="e", padx=10, pady=(0, 8))
            setattr(self, attr, lbl)

        _stat_box(stats, "میانگین مبدا",    "_cr_src",  C["blue"],  0, 1)
        _stat_box(stats, "میانگین مقصد",    "_cr_dst",  C["text2"], 0, 0)
        _stat_box(stats, "اختلاف",          "_cr_diff", C["gold"],  1, 1)
        _stat_box(stats, "وضعیت",           "_cr_stat", C["text2"], 1, 0)

        # کارت قیمت پیشنهادی
        self._cr_price_card = ctk.CTkFrame(result_col, fg_color=C["buy_dim"],
                                           corner_radius=14, border_width=1,
                                           border_color=C["buy_glow"])
        self._cr_price_card.pack(fill="x", padx=12, pady=(4, 8))
        ctk.CTkFrame(self._cr_price_card, height=4, fg_color=C["buy"],
                     corner_radius=0).pack(fill="x")
        self._label(self._cr_price_card, "قیمت پیشنهادی", 11, color=C["buy"]).pack(
            anchor="e", padx=18, pady=(16, 0))
        self._cr_price_lbl = self._label(self._cr_price_card, "—", 34, True, color=C["buy"])
        self._cr_price_lbl.pack(anchor="e", padx=18, pady=(4, 16))

        self._send_btn = ctk.CTkButton(
            result_col, text="📤  ارسال به کانال مقصد",
            height=46, corner_radius=8,
            fg_color=C["teal"], hover_color=C["teal_hov"],
            text_color="#fff", font=_f(14, True),
            state="disabled", command=self._send_calc_result)
        self._send_btn.pack(fill="x", padx=12, pady=(0, 16))

        # لاگ ارسال
        self._calc_log = ctk.CTkTextbox(result_col, height=80,
                                        fg_color=C["input"], text_color=C["text2"],
                                        font=_f(10), corner_radius=8, border_width=0)
        self._calc_log.pack(fill="x", padx=12, pady=(0, 12))
        self._calc_log.configure(state="disabled")

        self._calc_price_value = None  # قیمت محاسبه‌شده برای ارسال

    def _get_channel_avg(self, name: str):
        for r in self.results:
            if r.get("channel") == name or r.get("url") == name:
                buy, sell = r.get("buy"), r.get("sell")
                if buy and sell:
                    return (buy + sell) / 2
                return buy or sell
        return None

    def _do_calc(self):
        src_name = self._calc_src_var.get()
        dst_name = self._calc_dst_var.get()

        if not self.results:
            messagebox.showwarning("بدون داده", "ابتدا استخراج را اجرا کنید.")
            return

        src_avg = self._get_channel_avg(src_name)
        dst_avg = self._get_channel_avg(dst_name)

        if src_avg is None:
            messagebox.showwarning("داده‌ای نیست", f"قیمتی برای کانال مبدا «{src_name}» پیدا نشد.")
            return
        if dst_avg is None:
            messagebox.showwarning("داده‌ای نیست", f"قیمتی برای کانال مقصد «{dst_name}» پیدا نشد.")
            return

        try:
            threshold  = float(self._calc_threshold_e.get().strip() or "0")
            deduction  = float(self._calc_deduction_e.get().strip() or "0")
        except ValueError:
            messagebox.showerror("خطا", "آستانه و کسر باید عدد باشند.")
            return

        diff = abs(src_avg - dst_avg)
        proposed = src_avg - deduction

        self._cr_src.configure(text=f"{src_avg:,.0f}")
        self._cr_dst.configure(text=f"{dst_avg:,.0f}")
        self._cr_diff.configure(text=f"{diff:,.0f}")

        if diff > threshold:
            status_txt   = f"✓ بیشتر از آستانه ({threshold:,.0f})"
            status_color = C["buy"]
            self._cr_price_card.configure(border_color=C["buy"], fg_color=C["buy_dim"])
            self._cr_price_lbl.configure(text=f"{proposed:,.0f}", text_color=C["buy"])
            self._send_btn.configure(state="normal")
            self._calc_price_value = proposed
        else:
            status_txt   = f"✗ کمتر از آستانه ({threshold:,.0f})"
            status_color = C["text3"]
            self._cr_price_card.configure(border_color=C["border2"], fg_color=C["input"])
            self._cr_price_lbl.configure(text=f"{proposed:,.0f}", text_color=C["text2"])
            self._send_btn.configure(state="normal")  # همیشه قابل ارسال
            self._calc_price_value = proposed

        self._cr_stat.configure(text=status_txt, text_color=status_color)

    def _save_calc_settings(self):
        self.settings["calc_source"]    = self._calc_src_var.get()
        self.settings["calc_dest"]      = self._calc_dst_var.get()
        self.settings["calc_threshold"] = self._calc_threshold_e.get().strip()
        self.settings["calc_deduction"] = self._calc_deduction_e.get().strip()
        save_settings(self.settings)
        messagebox.showinfo("ذخیره شد", "تنظیمات محاسبه ذخیره شد.")

    def _send_calc_result(self):
        if self._calc_price_value is None:
            messagebox.showwarning("محاسبه نشده", "ابتدا محاسبه را انجام دهید.")
            return

        token    = self.settings.get("bot_token", "").strip()
        chat_id  = self.settings.get("dest_channel", "").strip()
        template = self.settings.get("msg_template", "{قیمت}")
        buttons  = self.settings.get("inline_buttons", "")

        if not token or not chat_id:
            messagebox.showwarning("تنظیمات ناقص",
                                   "توکن ربات و آیدی کانال مقصد را در تب «فرمت خروجی» وارد کنید.")
            self._show_page("format")
            return

        jalali_date, time_str = shamsi_now()
        text = template.replace("{قیمت}", f"{self._calc_price_value:,.0f}") \
                       .replace("{تاریخ}", jalali_date) \
                       .replace("{ساعت}",  time_str)

        def _send():
            try:
                resp = bot_send_message(token, chat_id, text, buttons)
                ok   = resp.get("ok", False)
                self.after(0, lambda: self._calc_log_write(
                    f"✓ ارسال موفق — message_id: {resp.get('result', {}).get('message_id', '?')}"
                    if ok else f"✗ خطا: {resp}"))
            except Exception as e:
                self.after(0, lambda err=e: self._calc_log_write(f"✗ خطا در ارسال: {err}"))

        threading.Thread(target=_send, daemon=True).start()
        self._calc_log_write("در حال ارسال...")

    def _calc_log_write(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._calc_log.configure(state="normal")
        self._calc_log.insert("end", f"[{ts}] {msg}\n")
        self._calc_log.see("end")
        self._calc_log.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    # FORMAT PAGE — فرمت خروجی
    # ══════════════════════════════════════════════════════════════════════════
    def _build_format_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["format"] = page
        self._page_header(page, "فرمت پیام خروجی",
                          "تنظیم قالب پیام و دکمه‌های شیشه‌ای برای ارسال ربات")

        body = ctk.CTkScrollableFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # ─ کارت تنظیمات ربات ─────────────────────────────────────────────────
        bot_card = self._card(body)
        bot_card.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(bot_card, height=3, fg_color=C["blue"], corner_radius=0).pack(fill="x")
        self._label(bot_card, "اطلاعات ربات", 13, True).pack(
            anchor="e", padx=16, pady=(14, 8))

        def _sfield(lbl, attr, ph, key, secret=False):
            r = ctk.CTkFrame(bot_card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=5)
            self._label(r, lbl, 11, color=C["text2"]).pack(anchor="e", fill="x", pady=(0, 3))
            e = self._entry(r, ph, secret=secret, value=self.settings.get(key, ""))
            e.pack(fill="x")
            setattr(self, attr, e)

        _sfield("توکن ربات (Bot Token)", "_fmt_token_e",
                "123456:ABCdef...", "bot_token")
        _sfield("آیدی کانال مقصد", "_fmt_chat_e",
                "@channel_name یا -100xxxxxxxxxx", "dest_channel")

        # ─ کارت قالب پیام ────────────────────────────────────────────────────
        tmpl_card = self._card(body)
        tmpl_card.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(tmpl_card, height=3, fg_color=C["teal"], corner_radius=0).pack(fill="x")

        hdr = ctk.CTkFrame(tmpl_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        self._label(hdr, "قالب پیام", 13, True).pack(side="right")
        self._label(hdr,
                    "{قیمت}  {تاریخ}  {ساعت}",
                    9, color=C["text3"]).pack(side="left")

        self._fmt_template = ctk.CTkTextbox(
            tmpl_card, height=110,
            fg_color=C["input"], border_color=C["border2"],
            border_width=1, text_color=C["text"], font=_f(12))
        self._fmt_template.pack(fill="x", padx=16)
        self._fmt_template.insert("1.0", self.settings.get(
            "msg_template",
            "نرخ تتر: {قیمت} تومان\nتاریخ: {تاریخ}\nساعت: {ساعت}"))

        # ─ کارت دکمه‌های شیشه‌ای ─────────────────────────────────────────────
        btn_card = self._card(body)
        btn_card.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(btn_card, height=3, fg_color=C["gold"], corner_radius=0).pack(fill="x")

        hdr2 = ctk.CTkFrame(btn_card, fg_color="transparent")
        hdr2.pack(fill="x", padx=16, pady=(14, 4))
        self._label(hdr2, "دکمه‌های شیشه‌ای (Inline Buttons)", 13, True).pack(side="right")
        self._label(hdr2, "متن | URL  —  چند دکمه در یک ردیف با ||",
                    9, color=C["text3"]).pack(side="left")

        self._fmt_buttons = ctk.CTkTextbox(
            btn_card, height=90,
            fg_color=C["input"], border_color=C["border2"],
            border_width=1, text_color=C["text"], font=_f(11))
        self._fmt_buttons.pack(fill="x", padx=16)
        self._fmt_buttons.insert("1.0", self.settings.get("inline_buttons", ""))

        self._label(btn_card,
                    "مثال:\nخرید | https://t.me/my_channel\n"
                    "فروش | https://t.me/my_channel || پشتیبانی | https://t.me/support",
                    9, color=C["text3"]).pack(anchor="e", padx=16, pady=(4, 10))

        # ─ کارت پیش‌نمایش ────────────────────────────────────────────────────
        prev_card = self._card(body)
        prev_card.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(prev_card, height=3, fg_color=C["sell"], corner_radius=0).pack(fill="x")
        self._label(prev_card, "پیش‌نمایش پیام", 13, True).pack(
            anchor="e", padx=16, pady=(14, 6))

        self._fmt_preview = ctk.CTkTextbox(
            prev_card, height=100,
            fg_color=C["bg2"], border_width=0, text_color=C["text2"],
            font=_f(11))
        self._fmt_preview.pack(fill="x", padx=16, pady=(0, 14))
        self._fmt_preview.configure(state="disabled")

        # ─ دکمه‌های عمل ──────────────────────────────────────────────────────
        act_row = ctk.CTkFrame(body, fg_color="transparent")
        act_row.pack(fill="x", pady=(0, 8))
        self._btn(act_row, "💾 ذخیره تنظیمات", self._save_format_settings,
                  primary=True, h=42).pack(side="right", padx=(6, 0))
        self._btn(act_row, "👁 پیش‌نمایش", self._preview_format,
                  primary=False, h=42).pack(side="right")

    def _preview_format(self):
        template = self._fmt_template.get("1.0", "end").strip()
        jalali_date, time_str = shamsi_now()
        sample_price = f"{166000:,}"
        text = template.replace("{قیمت}", sample_price) \
                       .replace("{تاریخ}", jalali_date) \
                       .replace("{ساعت}",  time_str)
        self._fmt_preview.configure(state="normal")
        self._fmt_preview.delete("1.0", "end")
        self._fmt_preview.insert("1.0", text)
        self._fmt_preview.configure(state="disabled")

    def _save_format_settings(self):
        self.settings["bot_token"]      = self._fmt_token_e.get().strip()
        self.settings["dest_channel"]   = self._fmt_chat_e.get().strip()
        self.settings["msg_template"]   = self._fmt_template.get("1.0", "end").strip()
        self.settings["inline_buttons"] = self._fmt_buttons.get("1.0", "end").strip()
        save_settings(self.settings)
        messagebox.showinfo("ذخیره شد", "تنظیمات فرمت خروجی ذخیره شد.")

    # ══════════════════════════════════════════════════════════════════════════
    # SETTINGS PAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_settings_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self.pages["settings"] = page
        self._page_header(page, "تنظیمات API تلگرام", "اطلاعات اتصال به حساب تلگرام")

        body = ctk.CTkScrollableFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # Info card
        info = self._card(body)
        info.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(info, height=3, fg_color=C["gold"], corner_radius=0).pack(
            fill="x")
        self._label(
            info,
            "برای استفاده، به سایت my.telegram.org مراجعه کنید.\n"
            "وارد شوید، گزینه «API development tools» را انتخاب کرده\n"
            "و API ID و API Hash خود را کپی کنید.",
            11, color=C["text2"]).pack(anchor="e", padx=16, pady=14)

        # Form card
        form = self._card(body)
        form.pack(fill="x", pady=(0, 12))
        self._label(form, "اطلاعات اتصال", 13, True).pack(
            anchor="e", padx=16, pady=(16, 12))

        self._sett_entries = {}
        fields = [
            ("api_id",   "API ID",        "عدد ۷ رقمی"),
            ("api_hash", "API Hash",       "رشته ۳۲ کاراکتری"),
            ("phone",    "شماره تلفن",    "+989xxxxxxxxx"),
        ]
        for key, label, ph in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            self._label(row, label, 12, color=C["text2"]).pack(
                anchor="e", fill="x", pady=(0, 4))
            e = self._entry(row, ph, value=self.settings.get(key, ""))
            e.pack(fill="x")
            self._sett_entries[key] = e

        ctk.CTkFrame(form, height=1, fg_color=C["border"]).pack(
            fill="x", padx=16, pady=8)

        self._btn(form, "💾  ذخیره تنظیمات",
                  self._save_settings, primary=True, h=42).pack(
            anchor="e", padx=16, pady=(0, 16))

        # Warning card
        warn = self._card(body)
        warn.pack(fill="x")
        ctk.CTkFrame(warn, height=3, fg_color=C["sell"], corner_radius=0).pack(
            fill="x")
        self._label(
            warn,
            "⚠  فایل session در کنار برنامه ذخیره می‌شود.\n"
            "اولین بار که استخراج را شروع می‌کنید، تلگرام کد تأیید ارسال می‌کند.",
            10, color=C["text3"]).pack(anchor="e", padx=16, pady=12)

    def _save_settings(self):
        for key, e in self._sett_entries.items():
            self.settings[key] = e.get().strip()
        save_settings(self.settings)
        messagebox.showinfo("ذخیره شد", "تنظیمات با موفقیت ذخیره شد.")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ChartoneXApp()
    app.mainloop()
