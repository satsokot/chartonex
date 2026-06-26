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
from tkinter import messagebox, ttk
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
PRICE_PATTERNS = [
    # "خرید: 98500" / "فروش: 99000"
    (r'خرید[\s:：\-]+([0-9][0-9,\.]+)', "buy"),
    (r'فروش[\s:：\-]+([0-9][0-9,\.]+)', "sell"),
    # "buy: 98500" / "sell: 99000"
    (r'buy[\s:：\-]+([0-9][0-9,\.]+)', "buy"),
    (r'sell[\s:：\-]+([0-9][0-9,\.]+)', "sell"),
    # "قیمت خرید تتر" patterns
    (r'قیمت\s*خرید[\s:：\-]+([0-9][0-9,\.]+)', "buy"),
    (r'قیمت\s*فروش[\s:：\-]+([0-9][0-9,\.]+)', "sell"),
    # USDT / tether with optional word between keyword and price
    (r'قیمت\s*خرید\s*\w*\s*[:\s]+([0-9][0-9,\.]+)', "buy"),
    (r'قیمت\s*فروش\s*\w*\s*[:\s]+([0-9][0-9,\.]+)', "sell"),
    (r'tether[\s\|خرید:]+([0-9][0-9,\.]+)', "buy"),
    # Arrow patterns: خرید ← 98500
    (r'خرید\s*[←→:]\s*([0-9][0-9,\.]+)', "buy"),
    (r'فروش\s*[←→:]\s*([0-9][0-9,\.]+)', "sell"),
]


def extract_prices(text: str):
    """Extract buy/sell prices from a message text. Returns dict with 'buy' and/or 'sell'."""
    text_lower = text.lower()
    prices = {}
    for pattern, side in PRICE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "").replace("٬", "")
            try:
                val = float(raw)
                if 1000 < val < 10_000_000:   # sanity check for toman/rial range
                    if side not in prices:
                        prices[side] = val
            except ValueError:
                pass
    return prices


# ── Telegram Client ───────────────────────────────────────────────────────────
async def fetch_channel_prices(api_id, api_hash, phone, channels, limit, progress_cb, result_cb, error_cb):
    """Connect to Telegram and read recent messages from each channel."""
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError, FloodWaitError
    except ImportError:
        error_cb("Telethon is not installed. Run: pip install telethon")
        return

    session_file = "chartonex_session"
    client = TelegramClient(session_file, int(api_id), api_hash)

    try:
        await client.start(phone=phone)
    except Exception as e:
        error_cb(f"خطا در اتصال به تلگرام:\n{e}")
        return

    results = []
    total = len(channels)

    for idx, ch in enumerate(channels):
        url = ch["url"].strip()
        progress_cb(idx, total, f"در حال خواندن: {url}")
        try:
            entity = await client.get_entity(url)
            async for msg in client.iter_messages(entity, limit=int(limit)):
                if msg.text:
                    prices = extract_prices(msg.text)
                    if prices:
                        results.append({
                            "channel": ch.get("name") or url,
                            "url": url,
                            "message_id": msg.id,
                            "date": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "",
                            "buy": prices.get("buy"),
                            "sell": prices.get("sell"),
                            "text_preview": msg.text[:120].replace("\n", " "),
                        })
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
        row2.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(row2, text="لینک کانال:", width=90,
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")
        self.ch_url_entry = ctk.CTkEntry(row2,
                                         placeholder_text="مثال: @usdt_iran یا https://t.me/channel",
                                         height=36, fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         text_color=COLORS["text_primary"])
        self.ch_url_entry.pack(side="left", fill="x", expand=True, padx=(6, 12))

        ctk.CTkButton(row2, text="+ افزودن", width=110, height=36,
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

    def _add_channel(self):
        name = self.ch_name_entry.get().strip()
        url = self.ch_url_entry.get().strip()

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
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        save_channels(self.channels)
        self.ch_name_entry.delete(0, "end")
        self.ch_url_entry.delete(0, "end")
        self._refresh_channel_list()

    def _refresh_channel_list(self):
        for widget in self.channel_scroll.winfo_children():
            widget.destroy()

        for idx, ch in enumerate(self.channels):
            self._build_channel_row(idx, ch)

        count = len(self.channels)
        self.ch_count_label.configure(text=f"{count} کانال")

    def _build_channel_row(self, idx, ch):
        row = ctk.CTkFrame(self.channel_scroll, fg_color=COLORS["bg_input"],
                            corner_radius=8, height=52)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text=str(idx + 1), width=32,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(12, 4))

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=8)

        ctk.CTkLabel(info_frame, text=ch.get("name", ch["url"]),
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_primary"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=ch["url"],
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=COLORS["text_secondary"],
                     anchor="w").pack(fill="x")

        ctk.CTkButton(row, text="✕", width=32, height=32,
                      corner_radius=6,
                      fg_color="transparent",
                      hover_color=COLORS["accent_red"],
                      text_color=COLORS["text_secondary"],
                      font=ctk.CTkFont("Segoe UI", 13),
                      command=lambda i=idx: self._remove_channel(i)).pack(side="right", padx=12)

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

        limit_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        limit_row.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(limit_row, text="تعداد پیام‌ها:", width=120,
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont("Segoe UI", 12)).pack(side="left")
        self.limit_slider = ctk.CTkSlider(limit_row, from_=5, to=100,
                                          number_of_steps=19,
                                          button_color=COLORS["accent"],
                                          button_hover_color=COLORS["accent_hover"],
                                          command=self._update_limit_label)
        self.limit_slider.set(int(self.settings.get("limit", 20)))
        self.limit_slider.pack(side="left", fill="x", expand=True, padx=12)
        self.limit_value_label = ctk.CTkLabel(limit_row, text=self.settings.get("limit", "20"),
                                              width=36,
                                              font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                              text_color=COLORS["accent"])
        self.limit_value_label.pack(side="left")

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

        self.status_label = ctk.CTkLabel(status_card, text="آماده برای شروع",
                                         font=ctk.CTkFont("Segoe UI", 11),
                                         text_color=COLORS["text_secondary"])
        self.status_label.pack(anchor="w", padx=16, pady=(0, 14))

        # Buttons
        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=8)

        self.start_btn = ctk.CTkButton(
            btn_row, text="▶  شروع استخراج",
            height=44, corner_radius=10,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self._start_scraping,
        )
        self.start_btn.pack(side="left", padx=(0, 12))

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

        ctk.CTkLabel(log_card, text="گزارش عملیات",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 6))

        self.log_text = ctk.CTkTextbox(log_card, fg_color=COLORS["bg_input"],
                                       text_color=COLORS["text_secondary"],
                                       font=ctk.CTkFont("Courier New", 11),
                                       corner_radius=8, border_width=0)
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")

    def _update_limit_label(self, val):
        self.limit_value_label.configure(text=str(int(val)))

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

        self.start_btn.configure(state="disabled", text="در حال اجرا...")
        self.progress_bar.set(0)
        self.results = []
        self._log(f"شروع استخراج از {len(self.channels)} کانال...")

        limit = int(self.limit_slider.get())

        def progress_cb(done, total, msg):
            self.after(0, lambda: self._on_progress(done, total, msg))

        def result_cb(results):
            self.after(0, lambda: self._on_results(results))

        def error_cb(msg):
            self.after(0, lambda: self._on_error(msg))

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                fetch_channel_prices(
                    s["api_id"], s["api_hash"], s["phone"],
                    self.channels, limit,
                    progress_cb, result_cb, error_cb
                )
            )
            loop.close()

        threading.Thread(target=run, daemon=True).start()

    def _on_progress(self, done, total, msg):
        frac = done / total if total else 0
        self.progress_bar.set(frac)
        self.status_label.configure(text=msg)
        self._log(msg)

    def _on_results(self, results):
        self.results = results
        self.start_btn.configure(state="normal", text="▶  شروع استخراج")
        self._log(f"✓ استخراج تمام شد. {len(results)} نتیجه یافت شد.")
        self._refresh_output()
        self._show_page("output")

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

        # Table frame
        table_card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"],
                                  corner_radius=12, border_width=1,
                                  border_color=COLORS["border"])
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
                        background=COLORS["bg_input"],
                        foreground=COLORS["text_primary"],
                        fieldbackground=COLORS["bg_input"],
                        borderwidth=0,
                        rowheight=36,
                        font=("Segoe UI", 11))
        style.configure("Dark.Treeview.Heading",
                        background=COLORS["bg_secondary"],
                        foreground=COLORS["text_secondary"],
                        relief="flat",
                        font=("Segoe UI", 11, "bold"))
        style.map("Dark.Treeview",
                  background=[("selected", COLORS["bg_card"])],
                  foreground=[("selected", COLORS["accent"])])

        cols = ("channel", "buy", "sell", "date", "preview")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                 style="Dark.Treeview")

        col_defs = [
            ("channel", "کانال", 160),
            ("buy", "خرید (تومان)", 130),
            ("sell", "فروش (تومان)", 130),
            ("date", "تاریخ", 130),
            ("preview", "پیش‌نمایش پیام", 400),
        ]
        for col_id, heading, width in col_defs:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor="center" if col_id != "preview" else "w")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 4))

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
        for item in self.tree.get_children():
            self.tree.delete(item)

        buys = [r["buy"] for r in self.results if r.get("buy")]
        sells = [r["sell"] for r in self.results if r.get("sell")]

        best_buy = f"{max(buys):,.0f}" if buys else "—"
        best_sell = f"{min(sells):,.0f}" if sells else "—"

        self.card_best_buy._value_label.configure(text=best_buy)
        self.card_best_sell._value_label.configure(text=best_sell)
        self.card_total._value_label.configure(text=str(len(self.results)))
        self.result_count_label.configure(text=f"{len(self.results)} نتیجه")

        for r in self.results:
            buy_str = f"{r['buy']:,.0f}" if r.get("buy") else "—"
            sell_str = f"{r['sell']:,.0f}" if r.get("sell") else "—"
            self.tree.insert("", "end", values=(
                r.get("channel", ""),
                buy_str,
                sell_str,
                r.get("date", ""),
                r.get("text_preview", ""),
            ))

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
