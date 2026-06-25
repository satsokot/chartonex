import logging
import jdatetime
from datetime import datetime, timezone

from bot.price_parser import parse_source_prices, parse_dest_price, calculate_average
from bot.telegram_reader import fetch_latest_messages, run_async
from bot.telegram_sender import send_price_message

logger = logging.getLogger(__name__)


def run_price_check(app):
    """Main scheduled job: check prices and send update if needed."""
    with app.app_context():
        from models import Settings, PriceLog
        from database import db

        cfg = _load_config()
        if not cfg:
            return

        log = PriceLog()

        # --- Read source channel ---
        source_texts = run_async(
            fetch_latest_messages(cfg['api_id'], cfg['api_hash'], cfg['source_channel'], limit=10)
        )
        source_buy, source_sell = _extract_source_prices(source_texts)
        log.source_buy = source_buy
        log.source_sell = source_sell

        if source_buy is None and source_sell is None:
            logger.warning("Could not parse source channel prices")
            log.action_taken = 'parse_error_source'
            db.session.add(log)
            db.session.commit()
            return

        source_avg = calculate_average(source_buy, source_sell)
        log.source_avg = source_avg

        # --- Read destination channel ---
        dest_texts = run_async(
            fetch_latest_messages(cfg['api_id'], cfg['api_hash'], cfg['dest_channel'], limit=3)
        )
        dest_price = _extract_dest_price(dest_texts)
        log.dest_price = dest_price

        if dest_price is None:
            logger.warning("Could not parse destination channel price")
            log.action_taken = 'parse_error_dest'
            db.session.add(log)
            db.session.commit()
            return

        difference = abs(dest_price - source_avg)
        log.difference = difference

        logger.info(
            f"Source avg={source_avg}, Dest={dest_price}, "
            f"Diff={difference}, Threshold={cfg['threshold']}"
        )

        if difference <= cfg['threshold']:
            log.action_taken = 'no_action'
            db.session.add(log)
            db.session.commit()
            return

        # --- Calculate and send new price ---
        new_price = round(source_avg - cfg['deduction'])
        log.sent_price = new_price

        message_text = _build_message(new_price, cfg['message_template'])
        last_msg_id = cfg.get('last_sent_message_id')
        edit_id = int(last_msg_id) if last_msg_id else None

        result = send_price_message(
            bot_token=cfg['bot_token'],
            channel=cfg['dest_channel'],
            text=message_text,
            button1_text=cfg['button1_text'],
            button1_url=cfg['button1_url'],
            button2_text=cfg['button2_text'],
            button2_url=cfg['button2_url'],
            edit_message_id=edit_id,
        )

        if result.get('ok'):
            new_id = result.get('message_id')
            Settings.set('last_sent_message_id', str(new_id) if new_id else '')
            log.message_id = new_id
            log.action_taken = 'sent'
            logger.info(f"Price update sent: {new_price} toman")
        else:
            log.action_taken = 'send_error'
            logger.error(f"Failed to send message: {result.get('error')}")

        db.session.add(log)
        db.session.commit()


def _load_config() -> dict | None:
    from models import Settings
    cfg = {
        'api_id': Settings.get('api_id', ''),
        'api_hash': Settings.get('api_hash', ''),
        'source_channel': Settings.get('source_channel', ''),
        'dest_channel': Settings.get('dest_channel', ''),
        'bot_token': Settings.get('bot_token', ''),
        'threshold': float(Settings.get('difference_threshold', '300') or 300),
        'deduction': float(Settings.get('price_deduction', '100') or 100),
        'message_template': Settings.get('message_template', 'قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}'),
        'button1_text': Settings.get('button1_text', ''),
        'button1_url': Settings.get('button1_url', ''),
        'button2_text': Settings.get('button2_text', ''),
        'button2_url': Settings.get('button2_url', ''),
        'last_sent_message_id': Settings.get('last_sent_message_id', ''),
    }

    missing = [k for k in ('api_id', 'api_hash', 'source_channel', 'dest_channel', 'bot_token') if not cfg[k]]
    if missing:
        logger.warning(f"Missing config keys: {missing}")
        return None

    try:
        cfg['api_id'] = int(cfg['api_id'])
    except ValueError:
        logger.error("api_id must be integer")
        return None

    return cfg


def _extract_source_prices(texts: list[str]) -> tuple:
    buy, sell = None, None
    for text in texts:
        parsed = parse_source_prices(text)
        if parsed['buy'] is not None and buy is None:
            buy = parsed['buy']
        if parsed['sell'] is not None and sell is None:
            sell = parsed['sell']
        if buy is not None and sell is not None:
            break
    return buy, sell


def _extract_dest_price(texts: list[str]) -> float | None:
    for text in texts:
        price = parse_dest_price(text)
        if price is not None:
            return price
    return None


def _build_message(price: float, template: str) -> str:
    now_jalali = jdatetime.datetime.now()
    date_str = now_jalali.strftime('%Y/%m/%d')
    return template.format(
        price=f"{int(price):,}",
        date=date_str,
    )
