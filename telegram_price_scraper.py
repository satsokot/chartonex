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
    "bg":         "#070B14",
    "bg2":        "#0D1526",
    "card":       "#111E35",
    "input":      "#162133",
    "border":     "#1E3050",
    "border2":    "#2A4070",
    "blue":       "#4F8EF7",
    "blue_hov":   "#3A7AE8",
    "teal":       "#00C9A7",
    "teal_hov":   "#00B396",
    "buy":        "#00C07F",
    "buy_dim":    "#0A2E1F",
    "sell":       "#FF4D6D",
    "sell_dim":   "#2E0A13",
    "gold":       "#FFB800",
    "text":       "#EEF2FF",
    "text2":      "#7B90BB",
    "text3":      "#3A5280",
    "red":        "#FF4D6D",
    "red_hov":    "#E03060",
    "green":      "#00C07F",
    "sidebar":    "#0A1020",
    "sidebar_hov":"#0F1A30",
    "active_bar": "#4F8EF7",
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
    defaults = {"api_id": "", "api_hash": "", "phone": "", "interval": 60}
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
FONT_PRICE  = ("Segoe UI", 26, "bold")
FONT_NAV    = ("Segoe UI", 13)


def _f(size, bold=False):
    return ctk.CTkFont("Segoe UI", size, "bold" if bold else "normal")


class ChartoneXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ChartoneX")
        self.geometry("1160x720")
        self.minsize(960, 620)
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
        # RTL: sidebar on right, content on left
        self.main_area = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self, width=210, fg_color=C["sidebar"], corner_radius=0)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        self.pages = {}
        self._content = ctk.CTkFrame(self.main_area, fg_color=C["bg"], corner_radius=0)
        self._content.pack(fill="both", expand=True)

        self._build_output_page()
        self._build_channels_page()
        self._build_scrape_page()
        self._build_settings_page()

        self._show_page("output")
        self._bind_paste_everywhere()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        # Logo
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=16, pady=(28, 4))

        ctk.CTkLabel(logo, text="◈ ChartoneX",
                     font=_f(18, True), text_color=C["blue"],
                     anchor="e").pack(fill="x")
        ctk.CTkLabel(logo, text="قیمت تتر از تلگرام",
                     font=_f(10), text_color=C["text2"],
                     anchor="e").pack(fill="x")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"]).pack(
            fill="x", padx=0, pady=(16, 12))

        nav_items = [
            ("📊", "خروجی",   "output"),
            ("📡", "کانال‌ها", "channels"),
            ("🔍", "استخراج", "scrape"),
            ("⚙️", "تنظیمات", "settings"),
        ]
        self._nav_btns = {}
        self._nav_indicators = {}

        for icon, label, key in nav_items:
            wrapper = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44)
            wrapper.pack(fill="x", pady=1)
            wrapper.pack_propagate(False)

            # Active left-border indicator (on right side for RTL = right border)
            indicator = ctk.CTkFrame(wrapper, width=3, fg_color="transparent", corner_radius=0)
            indicator.pack(side="right", fill="y")
            self._nav_indicators[key] = indicator

            btn = ctk.CTkButton(
                wrapper,
                text=f"{label}  {icon}",
                anchor="e",
                height=44,
                corner_radius=0,
                fg_color="transparent",
                hover_color=C["sidebar_hov"],
                text_color=C["text2"],
                font=_f(13),
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(fill="both", expand=True)
            self._nav_btns[key] = btn

        # Status dot at bottom
        self._conn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._conn_frame.pack(side="bottom", fill="x", padx=16, pady=20)
        ctk.CTkLabel(self._conn_frame, text="v2.0",
                     font=_f(9), text_color=C["text3"],
                     anchor="e").pack(fill="x")

    def _show_page(self, key: str):
        for k, f in self.pages.items():
            f.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color=C["sidebar_hov"], text_color=C["blue"])
                self._nav_indicators[k].configure(fg_color=C["active_bar"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text2"])
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
                         height=38, fg_color=C["input"],
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
        kw = dict(height=h, corner_radius=10, font=_f(12, True),
                  command=cmd, text=text)
        if w:
            kw["width"] = w
        if primary:
            kw.update(fg_color=C["blue"], hover_color=C["blue_hov"],
                      text_color="#ffffff")
        else:
            kw.update(fg_color=C["card"], hover_color=C["input"],
                      border_width=1, border_color=C["border2"],
                      text_color=C["text2"])
        return ctk.CTkButton(parent, **kw)

    def _page_header(self, page, title, subtitle=""):
        bar = ctk.CTkFrame(page, fg_color=C["bg2"], corner_radius=0, height=62)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28)
        self._label(inner, title, 17, True, anchor="e").pack(
            side="right", pady=(14, 2))
        if subtitle:
            self._label(inner, subtitle, 10, color=C["text2"],
                        anchor="e").pack(side="right", pady=(0, 14))
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
        card = self._card(parent)
        ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).pack(
            fill="x", padx=0, pady=(0, 0))
        self._label(card, label, 10, color=C["text2"]).pack(
            fill="x", padx=14, pady=(10, 2))
        val_lbl = self._label(card, value, 18, True, color=color)
        val_lbl.pack(fill="x", padx=14, pady=(0, 12))
        card._val = val_lbl
        return card

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
        is_single = has_buy != has_sell  # تک‌نرخی: فقط یکی دارد

        card = self._card(grid)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        # Channel name header
        hdr = ctk.CTkFrame(card, fg_color=C["input"], corner_radius=10)
        hdr.pack(fill="x", padx=10, pady=(10, 8))

        self._label(hdr, r.get("channel", "")[:30], 12, True).pack(
            side="right", padx=12, pady=8)

        # نشان «تک‌نرخی» برای کانال‌های تک‌نرخی
        if is_single:
            self._label(hdr, "تک‌نرخی", 9, color=C["gold"]).pack(
                side="left", padx=4, pady=8)
        self._label(hdr, r.get("date", ""), 9, color=C["text3"]).pack(
            side="left", padx=8, pady=8)

        prices_row = ctk.CTkFrame(card, fg_color="transparent")
        prices_row.pack(fill="x", padx=10, pady=(0, 10))

        if is_single:
            # ── یک کادر میانگین قیمت ─────────────────────────────────────────
            single_val = r.get("buy") or r.get("sell")
            avg_box = ctk.CTkFrame(prices_row, fg_color=C["input"],
                                   corner_radius=10, border_width=1,
                                   border_color=C["gold"])
            avg_box.pack(fill="both", expand=True)
            self._label(avg_box, "میانگین قیمت", 11, color=C["gold"]).pack(
                anchor="e", padx=16, pady=(12, 0))
            self._label(avg_box, f"{single_val:,.0f}", 24, True,
                        color=C["gold"]).pack(anchor="e", padx=16, pady=(0, 12))

        else:
            # ── دو‌نرخی: خرید + فروش (رفتار قبلی) ──────────────────────────
            sell_box = ctk.CTkFrame(prices_row, fg_color=C["sell_dim"],
                                    corner_radius=10, border_width=1,
                                    border_color=C["sell"])
            sell_box.pack(side="left", fill="both", expand=True, padx=(0, 4))
            self._label(sell_box, "فروش", 10, color=C["sell"]).pack(
                anchor="e", padx=12, pady=(10, 0))
            sell_val = f"{r['sell']:,.0f}" if has_sell else "—"
            self._label(sell_box, sell_val, 20, True, color=C["sell"]).pack(
                anchor="e", padx=12, pady=(0, 10))

            buy_box = ctk.CTkFrame(prices_row, fg_color=C["buy_dim"],
                                   corner_radius=10, border_width=1,
                                   border_color=C["buy"])
            buy_box.pack(side="right", fill="both", expand=True, padx=(4, 0))
            self._label(buy_box, "خرید", 10, color=C["buy"]).pack(
                anchor="e", padx=12, pady=(10, 0))
            buy_val = f"{r['buy']:,.0f}" if has_buy else "—"
            self._label(buy_box, buy_val, 20, True, color=C["buy"]).pack(
                anchor="e", padx=12, pady=(0, 10))

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

        row = ctk.CTkFrame(self._ch_scroll, fg_color=C["input"],
                           corner_radius=10)
        row.pack(fill="x", pady=4)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        # Delete button (left, RTL = appears left)
        ctk.CTkButton(top, text="✕", width=26, height=26,
                      corner_radius=6, fg_color="transparent",
                      hover_color=C["red"], text_color=C["text3"],
                      font=_f(11),
                      command=lambda i=idx: self._remove_channel(i)).pack(side="left")

        # Badge
        if sample:
            badge_txt   = "✓ شناسایی شد" if has_prices else "✗ ناشناخته"
            badge_color = C["buy"] if has_prices else C["sell"]
        else:
            badge_txt, badge_color = "⚠ بدون نمونه", C["gold"]

        ctk.CTkLabel(top, text=badge_txt,
                     font=_f(9), text_color=badge_color).pack(side="left", padx=8)

        # Channel info (right side)
        self._label(top, ch.get("name", ch["url"]), 12, True).pack(side="right")

        self._label(row, ch["url"], 10, color=C["text3"]).pack(
            anchor="e", padx=12, pady=(0, 6))

        if sample:
            prev = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=6)
            prev.pack(fill="x", padx=12, pady=(0, 10))
            self._label(prev, sample[:100].replace("\n", " ↵ "),
                        9, color=C["text3"]).pack(anchor="e", padx=8, pady=4)

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
            prog_card, height=8, progress_color=C["blue"],
            fg_color=C["input"], corner_radius=4)
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
            btn_card, text="⏹  توقف", height=46, corner_radius=10,
            fg_color=C["red"], hover_color=C["red_hov"],
            text_color="#fff", font=_f(13, True),
            state="disabled", command=self._stop_scraping)
        self._stop_btn.pack(side="right", padx=(6, 0))

        self._start_btn = ctk.CTkButton(
            btn_card, text="▶  شروع استخراج", height=46, corner_radius=10,
            fg_color=C["teal"], hover_color=C["teal_hov"],
            text_color="#fff", font=_f(13, True),
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
