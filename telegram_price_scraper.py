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
COLORS = {
    "bg_primary":    "#0D1117",
    "bg_secondary":  "#161B22",
    "bg_card":       "#1C2128",
    "bg_input":      "#21262D",
    "accent":        "#00D4AA",
    "accent_hover":  "#00B896",
    "accent_red":    "#F85149",
    "accent_yellow": "#E3B341",
    "text_primary":  "#F0F6FC",
    "text_secondary":"#8B949E",
    "border":        "#30363D",
    "buy_color":     "#3FB950",
    "sell_color":    "#F85149",
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
    defaults = {"api_id": "", "api_hash": "", "phone": "", "limit": "20"}
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
    # ── فرمت کانال Toman_to_Tether ──────────────────────────────
    # 💰#تتر[USDT] 166,232خرید🔹  (عدد قبل از خرید/فروش)
    (rf'تتر\s*\[?USDT\]?\s*{NUM}\s*خرید', "buy"),
    (rf'تتر\s*\[?USDT\]?\s*{NUM}\s*فروش', "sell"),
    # ◈ خرید[USDT] 166,235 ◈  (عدد بعد از خرید/فروش)
    (rf'خرید\s*\[?USDT\]?\s*{NUM}', "buy"),
    (rf'فروش\s*\[?USDT\]?\s*{NUM}', "sell"),

    # ── فرمت کانال cafebtc ───────────────────────────────────────
    # قیمت تتر : 165200 تومان
    (rf'قیمت\s*تتر\s*[:\-]?\s*{NUM}', "buy"),

    # ── فرمت‌های عمومی ───────────────────────────────────────────
    (rf'خرید\s*[:\-|]\s*{NUM}', "buy"),
    (rf'فروش\s*[:\-|]\s*{NUM}', "sell"),
    (rf'buy\s*[:\-|]\s*{NUM}', "buy"),
    (rf'sell\s*[:\-|]\s*{NUM}', "sell"),
    (rf'قیمت\s*خرید[^\d۰-۹٠-٩]{{0,15}}{NUM}', "buy"),
    (rf'قیمت\s*فروش[^\d۰-۹٠-٩]{{0,15}}{NUM}', "sell"),
    (rf'خرید\s*[←→➡⬅🔴🟢✅◈◆◇]?\s*{NUM}', "buy"),
    (rf'فروش\s*[←→➡⬅🔴🟢✅◈◆◇]?\s*{NUM}', "sell"),
    (rf'تتر\s*[:\-]?\s*خرید\s*[:\-]?\s*{NUM}', "buy"),
    (rf'تتر\s*[:\-]?\s*فروش\s*[:\-]?\s*{NUM}', "sell"),
    (rf'نرخ\s*خرید[^\d۰-۹٠-٩]{{0,10}}{NUM}', "buy"),
    (rf'نرخ\s*فروش[^\d۰-۹٠-٩]{{0,10}}{NUM}', "sell"),
]


def _to_float(raw: str):
    """Convert Persian/Arabic digits and remove separators, return float or None."""
    cleaned = raw.translate(FA_DIGITS).replace(",", "").replace("،", "").replace("٬", "").strip()
    try:
        val = float(cleaned)
        return val if 10_000 < val < 100_000_000 else None
    except ValueError:
        return None


def extract_prices(text: str):
    """Extract buy/sell prices from a message text. Returns dict with 'buy' and/or 'sell'."""
    prices = {}
    for pattern, side in PRICE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = _to_float(m.group(1))
            if val and side not in prices:
                prices[side] = val
    return prices


# ── Telegram Client ───────────────────────────────────────────────────────────
async def fetch_channel_prices(api_id, api_hash, phone, channels, limit, progress_cb, result_cb, error_cb, code_cb, password_cb):
    """Connect to Telegram and read recent messages from each channel."""
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError, FloodWaitError
    except ImportError:
        error_cb("Telethon is not installed. Run: pip install telethon")
        return

    # Session next to the script file so it persists across runs
    session_file = str(Path(__file__).parent / "chartonex_session")
    client = TelegramClient(session_file, int(api_id), api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.start(
                phone=phone,
                code_callback=code_cb,
                password=password_cb,
            )
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
            latest_buy = None
            latest_sell = None
            latest_buy_date = ""
            latest_sell_date = ""
            latest_buy_preview = ""
            latest_sell_preview = ""
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
            found_in_channel = 1 if (latest_buy or latest_sell) else 0
            if found_in_channel:
                results.append({
                    "channel": ch.get("name") or url,
                    "url": url,
                    "date": latest_buy_date or latest_sell_date,
                    "buy": latest_buy,
                    "sell": latest_sell,
                    "text_preview": latest_buy_preview or latest_sell_preview,
                })
            if found_in_channel == 0:
                progress_cb(idx, total, f"⚠ هیچ قیمتی در {url} یافت نشد — نمونه پیام‌های خام:")
                count = 0
                async for msg in client.iter_messages(entity, limit=5):
                    if msg.text and count < 3:
                        preview = msg.text[:300].replace("\n", " | ")
                        progress_cb(idx, total, f"  ▶ {preview}")
                        count += 1
        except FloodWaitError as e:
            error_cb(f"Flood wait از تلگرام: {e.seconds} ثانیه صبر کنید")
            break
        except Exception as e:
            results.append({
                "channel": url,
                "url": url,
                "message_id": None,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "buy": None,
                "sell": None,
                "text_preview": f"خطا: {e}",
            })

    await client.disconnect()
    progress_cb(total, total, "اتمام")
    result_cb(results)


# ══════════════════════════════════════════════════════════════════════════════
# GUI
# ══════════════════════════════════════════════════════════════════════════════

class ChartoneXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ChartoneX — استخراج قیمت تتر")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_primary"])

        self.channels = load_channels()
        self.settings = load_settings()
        self.results = []
        self._running = False          # auto-refresh loop flag
        self._stop_flag = threading.Event()
        self._next_run_after_id = None

        self._build_ui()
        self._refresh_channel_list()

    # ── UI Layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["bg_secondary"],
                                    corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # Main content area
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.main_frame.pack(side="left", fill="both", expand=True)

        # Notebook (tab-based pages)
        self.pages = {}
        self._content_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["bg_primary"],
                                            corner_radius=0)
        self._content_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_channels_page()
        self._build_scrape_page()
        self._build_output_page()
        self._build_settings_page()

        self._show_page("channels")
        self._bind_paste_to_all_entries()

    def _bind_paste_to_all_entries(self):
        """Enable Ctrl+V and right-click paste on all CTkEntry and CTkTextbox widgets."""
        def bind_entry(widget):
            if isinstance(widget, ctk.CTkEntry):
                inner = widget._entry
                inner.bind("<Control-v>", lambda e: self._paste(inner))
                inner.bind("<Control-V>", lambda e: self._paste(inner))
                inner.bind("<Button-3>", lambda e: self._show_paste_menu(e, inner))
            elif isinstance(widget, ctk.CTkTextbox):
                inner = widget._textbox
                inner.bind("<Control-v>", lambda e: self._paste_textbox(inner))
                inner.bind("<Control-V>", lambda e: self._paste_textbox(inner))
                inner.bind("<Button-3>", lambda e: self._show_paste_menu(e, inner))
            for child in widget.winfo_children():
                bind_entry(child)
        bind_entry(self)

    def _paste_textbox(self, textbox_widget):
        try:
            text = self.clipboard_get()
            textbox_widget.insert(tk.INSERT, text)
        except Exception:
            pass
        return "break"

    def _paste(self, entry_widget):
        try:
            text = self.clipboard_get()
            entry_widget.insert(tk.INSERT, text)
        except Exception:
            pass
        return "break"

    def _show_paste_menu(self, event, entry_widget):
        menu = tk.Menu(self, tearoff=0,
                       bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                       activebackground=COLORS["accent"], activeforeground="#000000",
                       font=("Segoe UI", 11))
        menu.add_command(label="پیست (Paste)", command=lambda: self._paste(entry_widget))
        menu.add_command(label="انتخاب همه", command=lambda: entry_widget.select_range(0, "end"))
        menu.tk_popup(event.x_root, event.y_root)

    def _build_sidebar(self):
        # Logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))

        ctk.CTkLabel(logo_frame, text="⬡ ChartoneX",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=COLORS["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="استخراج قیمت تتر",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=12, pady=(12, 20))

        nav_items = [
            ("📡", "کانال‌ها", "channels"),
            ("🔍", "استخراج", "scrape"),
            ("📊", "خروجی", "output"),
            ("⚙️", "تنظیمات", "settings"),
        ]
        self._nav_buttons = {}
        for icon, label, key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS["bg_card"],
                text_color=COLORS["text_secondary"],
                font=ctk.CTkFont("Segoe UI", 13),
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

        # Version at bottom
        ctk.CTkLabel(self.sidebar, text="v1.0.0",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=COLORS["text_secondary"]).pack(side="bottom", pady=16)

    def _show_page(self, key: str):
        for k, frame in self.pages.items():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["bg_card"], text_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])

    # ── Channels Page ─────────────────────────────────────────────────────────
    def _build_channels_page(self):
        page = ctk.CTkFrame(self._content_frame, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.pages["channels"] = page

        # Header
        header = ctk.CTkFrame(page, fg_color=COLORS["bg_secondary"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="مدیریت کانال‌های تلگرام",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=18)

        # Add channel card
        add_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                corner_radius=12, border_width=1,
                                border_color=COLORS["border"])
        add_card.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(add_card, text="افزودن کانال جدید",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        row1 = ctk.CTkFrame(add_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(row1, text="نام کانال:", width=90,
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")
        self.ch_name_entry = ctk.CTkEntry(row1, placeholder_text="مثال: صرافی آلفا",
                                          height=36, fg_color=COLORS["bg_input"],
                                          border_color=COLORS["border"],
                                          text_color=COLORS["text_primary"])
        self.ch_name_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        row2 = ctk.CTkFrame(add_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(row2, text="لینک کانال:", width=90,
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")
        self.ch_url_entry = ctk.CTkEntry(row2,
                                         placeholder_text="مثال: @usdt_iran یا https://t.me/channel",
                                         height=36, fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         text_color=COLORS["text_primary"])
        self.ch_url_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Sample message row
        row3 = ctk.CTkFrame(add_card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(row3, text="نمونه پیام:", width=90,
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left", anchor="n", pady=4)

        sample_col = ctk.CTkFrame(row3, fg_color="transparent")
        sample_col.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.ch_sample_entry = ctk.CTkTextbox(sample_col, height=72,
                                              fg_color=COLORS["bg_input"],
                                              border_color=COLORS["border"],
                                              border_width=1,
                                              text_color=COLORS["text_primary"],
                                              font=ctk.CTkFont("Segoe UI", 11))
        self.ch_sample_entry.pack(fill="x")
        self.ch_sample_entry.insert("end", "")

        # Test result label
        self.ch_test_label = ctk.CTkLabel(sample_col, text="یک نمونه پیام از کانال paste کنید",
                                          font=ctk.CTkFont("Segoe UI", 10),
                                          text_color=COLORS["text_secondary"],
                                          anchor="w")
        self.ch_test_label.pack(fill="x", pady=(2, 0))

        # Test button + Add button
        row4 = ctk.CTkFrame(add_card, fg_color="transparent")
        row4.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(row4, text="🔍 تست استخراج", width=130, height=34,
                      corner_radius=8,
                      fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
                      border_width=1, border_color=COLORS["border"],
                      text_color=COLORS["text_primary"],
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._test_sample).pack(side="left", padx=(0, 8))

        ctk.CTkButton(row4, text="+ افزودن کانال", width=130, height=34,
                      corner_radius=8,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#000000",
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      command=self._add_channel).pack(side="left")

        # Channel list
        list_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                 corner_radius=12, border_width=1,
                                 border_color=COLORS["border"])
        list_card.pack(fill="both", expand=True, padx=24, pady=(8, 24))

        list_header = ctk.CTkFrame(list_card, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(list_header, text="کانال‌های ذخیره‌شده",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        self.ch_count_label = ctk.CTkLabel(list_header, text="0 کانال",
                                           font=ctk.CTkFont("Segoe UI", 11),
                                           text_color=COLORS["text_secondary"])
        self.ch_count_label.pack(side="right")

        # Scrollable list
        self.channel_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.channel_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def _test_sample(self):
        sample = self.ch_sample_entry.get("1.0", "end").strip()
        if not sample:
            self.ch_test_label.configure(
                text="⚠ ابتدا یک نمونه پیام paste کنید", text_color=COLORS["accent_yellow"])
            return
        prices = extract_prices(sample)
        if prices:
            parts = []
            if "buy" in prices:
                parts.append(f"خرید: {prices['buy']:,.0f}")
            if "sell" in prices:
                parts.append(f"فروش: {prices['sell']:,.0f}")
            self.ch_test_label.configure(
                text="✓ استخراج موفق — " + "  |  ".join(parts),
                text_color=COLORS["buy_color"])
        else:
            self.ch_test_label.configure(
                text="✗ قیمتی یافت نشد — فرمت پیام را بررسی کنید",
                text_color=COLORS["accent_red"])

    def _add_channel(self):
        name = self.ch_name_entry.get().strip()
        url = self.ch_url_entry.get().strip()
        sample = self.ch_sample_entry.get("1.0", "end").strip()

        if not url:
            messagebox.showwarning("ورودی ناقص", "لطفاً لینک کانال را وارد کنید.")
            return

        # Normalize URL
        if not url.startswith("@") and "t.me/" not in url and not url.startswith("https://"):
            url = "@" + url

        for ch in self.channels:
            if ch["url"] == url:
                messagebox.showinfo("تکراری", "این کانال قبلاً اضافه شده است.")
                return

        self.channels.append({
            "name": name or url,
            "url": url,
            "sample": sample,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        save_channels(self.channels)
        self.ch_name_entry.delete(0, "end")
        self.ch_url_entry.delete(0, "end")
        self.ch_sample_entry.delete("1.0", "end")
        self.ch_test_label.configure(
            text="یک نمونه پیام از کانال paste کنید",
            text_color=COLORS["text_secondary"])
        self._refresh_channel_list()

    def _refresh_channel_list(self):
        for widget in self.channel_scroll.winfo_children():
            widget.destroy()

        for idx, ch in enumerate(self.channels):
            self._build_channel_row(idx, ch)

        count = len(self.channels)
        self.ch_count_label.configure(text=f"{count} کانال")

    def _build_channel_row(self, idx, ch):
        sample = ch.get("sample", "")
        prices = extract_prices(sample) if sample else {}
        has_prices = bool(prices)

        row = ctk.CTkFrame(self.channel_scroll, fg_color=COLORS["bg_input"],
                           corner_radius=8)
        row.pack(fill="x", pady=3)

        top = ctk.CTkFrame(row, fg_color="transparent", height=40)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text=str(idx + 1), width=32,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(12, 4))

        info_frame = ctk.CTkFrame(top, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=8)

        ctk.CTkLabel(info_frame, text=ch.get("name", ch["url"]),
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_primary"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=ch["url"],
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=COLORS["text_secondary"],
                     anchor="w").pack(fill="x")

        # Status badge
        if sample:
            badge_text = "✓ فرمت تشخیص داده شد" if has_prices else "✗ فرمت ناشناخته"
            badge_color = COLORS["buy_color"] if has_prices else COLORS["accent_red"]
        else:
            badge_text = "⚠ بدون نمونه"
            badge_color = COLORS["accent_yellow"]

        ctk.CTkLabel(top, text=badge_text,
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=badge_color).pack(side="right", padx=(0, 8))

        ctk.CTkButton(top, text="✕", width=28, height=28,
                      corner_radius=6,
                      fg_color="transparent",
                      hover_color=COLORS["accent_red"],
                      text_color=COLORS["text_secondary"],
                      font=ctk.CTkFont("Segoe UI", 12),
                      command=lambda i=idx: self._remove_channel(i)).pack(side="right", padx=(0, 8))

        # Show sample preview if exists
        if sample:
            preview_frame = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=4)
            preview_frame.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(preview_frame,
                         text=sample[:120].replace("\n", " ↵ "),
                         font=ctk.CTkFont("Courier New", 9),
                         text_color=COLORS["text_secondary"],
                         anchor="w",
                         wraplength=600).pack(anchor="w", padx=8, pady=4)

    def _remove_channel(self, idx):
        ch = self.channels[idx]
        if messagebox.askyesno("حذف کانال", f"آیا از حذف «{ch.get('name', ch['url'])}» مطمئن هستید؟"):
            self.channels.pop(idx)
            save_channels(self.channels)
            self._refresh_channel_list()

    # ── Scrape Page ───────────────────────────────────────────────────────────
    def _build_scrape_page(self):
        page = ctk.CTkFrame(self._content_frame, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.pages["scrape"] = page

        header = ctk.CTkFrame(page, fg_color=COLORS["bg_secondary"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="استخراج قیمت‌ها",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=18)

        # Config card
        cfg_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                corner_radius=12, border_width=1,
                                border_color=COLORS["border"])
        cfg_card.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(cfg_card, text="تنظیمات اجرا",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        interval_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        interval_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(interval_row, text="بازه تکرار:",
                     width=110, text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")

        # Preset interval buttons
        self._interval_seconds = int(self.settings.get("interval", 60))
        self._interval_var = tk.StringVar(value=str(self._interval_seconds))

        presets = [
            ("۳۰ ثانیه", 30),
            ("۱ دقیقه",  60),
            ("۵ دقیقه",  300),
            ("۱۵ دقیقه", 900),
            ("۳۰ دقیقه", 1800),
            ("۱ ساعت",   3600),
        ]
        self._preset_btns = {}
        btn_frame = ctk.CTkFrame(interval_row, fg_color="transparent")
        btn_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))

        for label, secs in presets:
            btn = ctk.CTkButton(
                btn_frame, text=label, width=80, height=30,
                corner_radius=6,
                fg_color=COLORS["accent"] if secs == self._interval_seconds else COLORS["bg_input"],
                hover_color=COLORS["accent_hover"],
                text_color="#000000" if secs == self._interval_seconds else COLORS["text_primary"],
                font=ctk.CTkFont("Segoe UI", 11),
                command=lambda s=secs, l=label: self._set_interval(s),
            )
            btn.pack(side="left", padx=3)
            self._preset_btns[secs] = btn

        self.interval_label = ctk.CTkLabel(interval_row,
                                           text=self._fmt_interval(self._interval_seconds),
                                           width=80,
                                           font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                           text_color=COLORS["accent"])
        self.interval_label.pack(side="left", padx=(10, 0))

        # Status + progress
        status_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                   corner_radius=12, border_width=1,
                                   border_color=COLORS["border"])
        status_card.pack(fill="x", padx=24, pady=8)

        self.progress_bar = ctk.CTkProgressBar(status_card, height=6,
                                               progress_color=COLORS["accent"],
                                               fg_color=COLORS["bg_input"])
        self.progress_bar.pack(fill="x", padx=16, pady=(14, 6))
        self.progress_bar.set(0)

        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=16, pady=(0, 14))

        self.status_label = ctk.CTkLabel(status_inner, text="آماده برای شروع",
                                         font=ctk.CTkFont("Segoe UI", 11),
                                         text_color=COLORS["text_secondary"])
        self.status_label.pack(side="left")

        self.countdown_label = ctk.CTkLabel(status_inner, text="",
                                            font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                            text_color=COLORS["accent_yellow"])
        self.countdown_label.pack(side="right")

        # Buttons
        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=8)

        self.start_btn = ctk.CTkButton(
            btn_row, text="▶  شروع",
            height=44, corner_radius=10,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self._start_scraping,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_row, text="⏹  توقف",
            height=44, corner_radius=10,
            fg_color=COLORS["accent_red"], hover_color="#C73E33",
            text_color="#ffffff",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            state="disabled",
            command=self._stop_scraping,
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="📊  مشاهده خروجی",
            height=44, corner_radius=10,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_input"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=lambda: self._show_page("output"),
        ).pack(side="left")

        # Log area
        log_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                corner_radius=12, border_width=1,
                                border_color=COLORS["border"])
        log_card.pack(fill="both", expand=True, padx=24, pady=(8, 24))

        log_header_row = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header_row.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(log_header_row, text="گزارش عملیات",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(log_header_row, text="📋 کپی همه",
                      width=90, height=26, corner_radius=6,
                      fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
                      text_color=COLORS["text_secondary"],
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._copy_log).pack(side="right")

        self.log_text = ctk.CTkTextbox(log_card, fg_color=COLORS["bg_input"],
                                       text_color=COLORS["text_secondary"],
                                       font=ctk.CTkFont("Courier New", 11),
                                       corner_radius=8, border_width=0)
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        inner_log = self.log_text._textbox
        inner_log.bind("<Control-c>", lambda e: self._copy_selected_log(inner_log))
        inner_log.bind("<Control-C>", lambda e: self._copy_selected_log(inner_log))
        inner_log.bind("<Control-a>", lambda e: self._select_all_log())
        inner_log.bind("<Control-A>", lambda e: self._select_all_log())
        inner_log.bind("<Button-3>", self._log_context_menu)
        self.log_text.configure(state="disabled")

    def _copy_selected_log(self, inner_widget):
        try:
            selected = inner_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def _copy_log(self):
        content = self.log_text._textbox.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def _select_all_log(self):
        inner = self.log_text._textbox
        inner.tag_add(tk.SEL, "1.0", "end")
        return "break"

    def _log_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0,
                       bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                       activebackground=COLORS["accent"], activeforeground="#000000",
                       font=("Segoe UI", 11))
        menu.add_command(label="کپی انتخاب‌شده", command=lambda: self._copy_selected_log(self.log_text._textbox))
        menu.add_command(label="انتخاب همه", command=self._select_all_log)
        menu.add_command(label="کپی همه", command=self._copy_log)
        menu.tk_popup(event.x_root, event.y_root)

    def _fmt_interval(self, secs: int) -> str:
        if secs < 60:
            return f"{secs} ثانیه"
        elif secs < 3600:
            return f"{secs // 60} دقیقه"
        else:
            return f"{secs // 3600} ساعت"

    def _set_interval(self, secs: int):
        self._interval_seconds = secs
        self.settings["interval"] = secs
        save_settings(self.settings)
        self.interval_label.configure(text=self._fmt_interval(secs))
        for s, btn in self._preset_btns.items():
            if s == secs:
                btn.configure(fg_color=COLORS["accent"], text_color="#000000")
            else:
                btn.configure(fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"])

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _start_scraping(self):
        if not self.channels:
            messagebox.showwarning("بدون کانال", "لطفاً ابتدا کانال‌هایی اضافه کنید.")
            return
        s = self.settings
        if not s.get("api_id") or not s.get("api_hash") or not s.get("phone"):
            messagebox.showwarning(
                "تنظیمات ناقص",
                "لطفاً API ID، API Hash و شماره تلفن را در صفحه «تنظیمات» وارد کنید."
            )
            self._show_page("settings")
            return

        self._running = True
        self._stop_flag.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._run_once()

    def _stop_scraping(self):
        self._running = False
        self._stop_flag.set()
        if self._next_run_after_id:
            self.after_cancel(self._next_run_after_id)
            self._next_run_after_id = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.countdown_label.configure(text="")
        self.status_label.configure(text="متوقف شد")
        self._log("⏹ استخراج متوقف شد.")

    def _run_once(self):
        if not self._running:
            return
        s = self.settings
        self.progress_bar.set(0)
        self.countdown_label.configure(text="")
        self._log(f"── شروع دور جدید استخراج از {len(self.channels)} کانال ──")

        def progress_cb(done, total, msg):
            self.after(0, lambda: self._on_progress(done, total, msg))

        def result_cb(results):
            self.after(0, lambda: self._on_results_auto(results))

        def error_cb(msg):
            self.after(0, lambda: self._on_error(msg))

        def code_cb():
            return self._ask_input(
                "کد تأیید تلگرام",
                "تلگرام یک کد برای شما فرستاد.\nکد را اینجا وارد کنید:"
            )

        def password_cb():
            return self._ask_input(
                "رمز دو مرحله‌ای",
                "حساب شما رمز دو مرحله‌ای دارد.\nرمز را وارد کنید:",
                secret=True
            )

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                fetch_channel_prices(
                    s["api_id"], s["api_hash"], s["phone"],
                    self.channels, 20,
                    progress_cb, result_cb, error_cb, code_cb, password_cb
                )
            )
            loop.close()

        threading.Thread(target=run, daemon=True).start()

    def _on_results_auto(self, results):
        """Handle results and schedule next run after interval."""
        self.results = results
        self._log(f"✓ {len(results)} نتیجه یافت شد.")
        self._refresh_output()
        self._show_page("output")
        if self._running:
            self._start_countdown(self._interval_seconds)

    def _start_countdown(self, remaining: int):
        if not self._running:
            return
        if remaining <= 0:
            self.countdown_label.configure(text="")
            self._run_once()
            return
        mins, secs = divmod(remaining, 60)
        if mins > 0:
            txt = f"دور بعدی: {mins:02d}:{secs:02d}"
        else:
            txt = f"دور بعدی: {secs} ثانیه"
        self.countdown_label.configure(text=txt)
        self._next_run_after_id = self.after(1000, lambda: self._start_countdown(remaining - 1))

    def _ask_input(self, title, prompt, secret=False):
        """Show a blocking dialog on the main thread and return the entered value."""
        result_holder = [None]
        event = threading.Event()

        def show():
            dialog = ctk.CTkToplevel(self)
            dialog.title(title)
            dialog.geometry("360x200")
            dialog.resizable(False, False)
            dialog.configure(fg_color=COLORS["bg_card"])
            dialog.grab_set()
            dialog.lift()
            dialog.focus_force()

            ctk.CTkLabel(dialog, text=prompt,
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=COLORS["text_primary"],
                         wraplength=320).pack(padx=24, pady=(24, 12))

            entry = ctk.CTkEntry(dialog, height=38, width=300,
                                 fg_color=COLORS["bg_input"],
                                 border_color=COLORS["accent"],
                                 text_color=COLORS["text_primary"],
                                 show="*" if secret else "")
            entry.pack(padx=24, pady=(0, 16))
            entry.focus()

            def confirm(e=None):
                result_holder[0] = entry.get().strip()
                dialog.destroy()
                event.set()

            entry.bind("<Return>", confirm)
            ctk.CTkButton(dialog, text="تأیید", height=36, width=120,
                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                          text_color="#000000",
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          command=confirm).pack()

            dialog.protocol("WM_DELETE_WINDOW", confirm)

        self.after(0, show)
        event.wait(timeout=120)
        return result_holder[0] or ""

    def _on_progress(self, done, total, msg):
        frac = done / total if total else 0
        self.progress_bar.set(frac)
        self.status_label.configure(text=msg)
        self._log(msg)


    def _on_error(self, msg):
        self.start_btn.configure(state="normal", text="▶  شروع استخراج")
        self._log(f"✗ خطا: {msg}")
        messagebox.showerror("خطا", msg)

    # ── Output Page ───────────────────────────────────────────────────────────
    def _build_output_page(self):
        page = ctk.CTkFrame(self._content_frame, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.pages["output"] = page

        header = ctk.CTkFrame(page, fg_color=COLORS["bg_secondary"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="قیمت‌های استخراج‌شده",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=18)

        self.result_count_label = ctk.CTkLabel(header, text="",
                                               font=ctk.CTkFont("Segoe UI", 12),
                                               text_color=COLORS["text_secondary"])
        self.result_count_label.pack(side="right", padx=24)

        # Summary cards
        summary_row = ctk.CTkFrame(page, fg_color="transparent")
        summary_row.pack(fill="x", padx=24, pady=(16, 8))

        self.card_best_buy = self._make_stat_card(summary_row, "بهترین قیمت خرید", "—", COLORS["buy_color"])
        self.card_best_buy.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_best_sell = self._make_stat_card(summary_row, "بهترین قیمت فروش", "—", COLORS["sell_color"])
        self.card_best_sell.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.card_total = self._make_stat_card(summary_row, "تعداد نتایج", "0", COLORS["accent"])
        self.card_total.pack(side="left", fill="x", expand=True)

        # Table header row
        table_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                  corner_radius=12, border_width=1,
                                  border_color=COLORS["border"])
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 4))

        # Column header
        col_header = ctk.CTkFrame(table_card, fg_color=COLORS["bg_secondary"], corner_radius=0, height=36)
        col_header.pack(fill="x", padx=0, pady=(0, 0))
        col_header.pack_propagate(False)
        for text, w in [("کانال", 160), ("خرید (تومان)", 130), ("فروش (تومان)", 130), ("تاریخ", 130), ("پیش‌نمایش پیام", 0)]:
            ctk.CTkLabel(col_header, text=text, width=w if w else 0,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_secondary"],
                         anchor="center").pack(side="left", padx=4)

        # Scrollable rows
        self.output_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.output_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Export button
        btn_frame = ctk.CTkFrame(page, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkButton(btn_frame, text="💾  ذخیره CSV",
                      height=38, corner_radius=8,
                      fg_color=COLORS["bg_card"],
                      hover_color=COLORS["bg_input"],
                      border_width=1, border_color=COLORS["border"],
                      text_color=COLORS["text_primary"],
                      font=ctk.CTkFont("Segoe UI", 12),
                      command=self._export_csv).pack(side="left")

    def _make_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                            corner_radius=10, border_width=1,
                            border_color=COLORS["border"])
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(12, 2))
        lbl = ctk.CTkLabel(card, text=value,
                           font=ctk.CTkFont("Segoe UI", 20, "bold"),
                           text_color=color)
        lbl.pack(anchor="w", padx=14, pady=(0, 12))
        card._value_label = lbl
        return card

    def _refresh_output(self):
        # Clear old rows
        for w in self.output_scroll.winfo_children():
            w.destroy()

        buys  = [r["buy"]  for r in self.results if r.get("buy")]
        sells = [r["sell"] for r in self.results if r.get("sell")]

        self.card_best_buy._value_label.configure(
            text=f"{max(buys):,.0f}" if buys else "—")
        self.card_best_sell._value_label.configure(
            text=f"{min(sells):,.0f}" if sells else "—")
        self.card_total._value_label.configure(text=str(len(self.results)))
        self.result_count_label.configure(text=f"{len(self.results)} نتیجه")

        for i, r in enumerate(self.results):
            buy_str  = f"{r['buy']:,.0f}"  if r.get("buy")  else "—"
            sell_str = f"{r['sell']:,.0f}" if r.get("sell") else "—"
            row_bg = COLORS["bg_input"] if i % 2 == 0 else COLORS["bg_card"]

            row = ctk.CTkFrame(self.output_scroll, fg_color=row_bg,
                               corner_radius=4, height=38)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            def _cell(parent, text, width, color=COLORS["text_primary"], bold=False):
                ctk.CTkLabel(parent, text=text, width=width,
                             font=ctk.CTkFont("Segoe UI", 11, "bold" if bold else "normal"),
                             text_color=color,
                             anchor="center").pack(side="left", padx=4)

            _cell(row, r.get("channel", "")[:22], 160)
            _cell(row, buy_str,  130, COLORS["buy_color"],  bold=bool(r.get("buy")))
            _cell(row, sell_str, 130, COLORS["sell_color"], bold=bool(r.get("sell")))
            _cell(row, r.get("date", ""), 130, COLORS["text_secondary"])
            # Preview — rest of the width
            ctk.CTkLabel(row, text=r.get("text_preview", "")[:80],
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=COLORS["text_secondary"],
                         anchor="w").pack(side="left", fill="x", expand=True, padx=4)

    def _export_csv(self):
        if not self.results:
            messagebox.showinfo("خروجی خالی", "ابتدا استخراج را اجرا کنید.")
            return
        filename = f"prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        lines = ["channel,buy,sell,date,preview"]
        for r in self.results:
            preview = r.get("text_preview", "").replace(",", "،").replace("\n", " ")
            lines.append(f"{r.get('channel','')},{r.get('buy','')},{r.get('sell','')},{r.get('date','')},{preview}")
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("ذخیره شد", f"فایل ذخیره شد:\n{filename}")

    # ── Settings Page ─────────────────────────────────────────────────────────
    def _build_settings_page(self):
        page = ctk.CTkFrame(self._content_frame, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.pages["settings"] = page

        header = ctk.CTkFrame(page, fg_color=COLORS["bg_secondary"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="تنظیمات API تلگرام",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=18)

        info_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                 corner_radius=12, border_width=1,
                                 border_color=COLORS["border"])
        info_card.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(info_card,
                     text="ℹ️  برای استفاده از این برنامه، API تلگرام نیاز است.\n"
                          "به سایت my.telegram.org مراجعه کرده و API ID و API Hash خود را دریافت کنید.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_secondary"],
                     justify="right").pack(anchor="w", padx=16, pady=14)

        form_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                 corner_radius=12, border_width=1,
                                 border_color=COLORS["border"])
        form_card.pack(fill="x", padx=24, pady=8)

        fields = [
            ("api_id", "API ID:", "عدد 7 رقمی", False),
            ("api_hash", "API Hash:", "رشته 32 کاراکتری", False),
            ("phone", "شماره تلفن:", "مثال: +989123456789", False),
        ]
        self._setting_entries = {}
        for key, label, placeholder, is_pass in fields:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(row, text=label, width=100,
                         text_color=COLORS["text_secondary"],
                         font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")
            entry = ctk.CTkEntry(row, placeholder_text=placeholder,
                                 height=36, fg_color=COLORS["bg_input"],
                                 border_color=COLORS["border"],
                                 text_color=COLORS["text_primary"],
                                 show="*" if is_pass else "")
            entry.insert(0, self.settings.get(key, ""))
            entry.pack(side="left", fill="x", expand=True)
            self._setting_entries[key] = entry

        ctk.CTkButton(form_card, text="💾  ذخیره تنظیمات",
                      height=40, corner_radius=8,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="#000000",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self._save_settings).pack(anchor="w", padx=16, pady=(4, 16))

    def _save_settings(self):
        for key, entry in self._setting_entries.items():
            self.settings[key] = entry.get().strip()
        save_settings(self.settings)
        messagebox.showinfo("ذخیره شد", "تنظیمات با موفقیت ذخیره شد.")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ChartoneXApp()
    app.mainloop()
