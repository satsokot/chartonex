from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_defaults()


def _seed_defaults():
    from models import Settings
    defaults = {
        'source_channel': '',
        'dest_channel': '',
        'difference_threshold': '300',
        'price_deduction': '100',
        'check_interval_minutes': '5',
        'bot_token': '',
        'api_id': '',
        'api_hash': '',
        'phone': '',
        'button1_text': 'دانلود اپلیکیشن',
        'button1_url': '',
        'button2_text': 'پشتیبانی',
        'button2_url': '',
        'is_running': 'false',
        'last_sent_message_id': '',
        'message_template': 'قیمت تتر : {price} تومان 💵 USDT\n─────────────────\nتاریخ: {date}',
    }
    for key, value in defaults.items():
        existing = Settings.query.filter_by(key=key).first()
        if not existing:
            from database import db
            db.session.add(Settings(key=key, value=value))
    db.session.commit()
