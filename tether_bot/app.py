import logging
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config
from database import db, init_db
from models import Settings, PriceLog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)

# --- Scheduler ---
scheduler = BackgroundScheduler(timezone='Asia/Tehran')
_job_id = 'price_check'


def _schedule_job(interval_minutes: int):
    from bot.scheduler import run_price_check
    if scheduler.get_job(_job_id):
        scheduler.remove_job(_job_id)
    scheduler.add_job(
        func=run_price_check,
        args=[app],
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=_job_id,
        replace_existing=True,
        max_instances=1,
    )
    logger.info(f"Job scheduled every {interval_minutes} minutes")


scheduler.start()

# Auto-resume if was running before restart
with app.app_context():
    if Settings.get('is_running') == 'true':
        try:
            interval = int(Settings.get('check_interval_minutes', '5') or 5)
            _schedule_job(interval)
            logger.info("Auto-resumed scheduler from previous state")
        except Exception as e:
            logger.error(f"Failed to auto-resume: {e}")


# --- Auth ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if (username == app.config['ADMIN_USERNAME'] and
                password == app.config['ADMIN_PASSWORD']):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'نام کاربری یا رمز عبور اشتباه است'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Admin Dashboard ---
@app.route('/')
@login_required
def admin_dashboard():
    settings = {row.key: row.value for row in Settings.query.all()}
    logs = PriceLog.query.order_by(PriceLog.id.desc()).limit(20).all()
    job = scheduler.get_job(_job_id)
    is_running = job is not None and job.next_run_time is not None
    return render_template(
        'admin/dashboard.html',
        settings=settings,
        logs=logs,
        is_running=is_running,
    )


@app.route('/settings', methods=['POST'])
@login_required
def save_settings():
    fields = [
        'source_channel', 'dest_channel', 'difference_threshold',
        'price_deduction', 'check_interval_minutes', 'bot_token',
        'api_id', 'api_hash', 'phone',
        'button1_text', 'button1_url', 'button2_text', 'button2_url',
        'message_template',
    ]
    for field in fields:
        value = request.form.get(field, '').strip()
        Settings.set(field, value)
    flash('تنظیمات با موفقیت ذخیره شد', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/bot/start', methods=['POST'])
@login_required
def bot_start():
    interval = int(Settings.get('check_interval_minutes', '5') or 5)
    _schedule_job(interval)
    Settings.set('is_running', 'true')
    return jsonify({'ok': True, 'message': f'ربات شروع به کار کرد (هر {interval} دقیقه)'})


@app.route('/bot/stop', methods=['POST'])
@login_required
def bot_stop():
    if scheduler.get_job(_job_id):
        scheduler.remove_job(_job_id)
    Settings.set('is_running', 'false')
    return jsonify({'ok': True, 'message': 'ربات متوقف شد'})


@app.route('/bot/run-now', methods=['POST'])
@login_required
def bot_run_now():
    from bot.scheduler import run_price_check
    try:
        run_price_check(app)
        return jsonify({'ok': True, 'message': 'بررسی قیمت انجام شد'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/bot/status')
@login_required
def bot_status():
    job = scheduler.get_job(_job_id)
    is_running = job is not None and job.next_run_time is not None
    next_run = job.next_run_time.strftime('%H:%M:%S') if is_running and job.next_run_time else None
    last_log = PriceLog.query.order_by(PriceLog.id.desc()).first()
    return jsonify({
        'is_running': is_running,
        'next_run': next_run,
        'last_log': last_log.to_dict() if last_log else None,
    })


@app.route('/logs')
@login_required
def logs_api():
    page = request.args.get('page', 1, type=int)
    logs = PriceLog.query.order_by(PriceLog.id.desc()).paginate(page=page, per_page=50)
    return jsonify({
        'logs': [l.to_dict() for l in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'page': page,
    })


# --- Telegram Auth Routes ---
@app.route('/telegram/connect', methods=['POST'])
@login_required
def telegram_connect():
    from bot.telegram_reader import start_client, run_async
    api_id_str = Settings.get('api_id', '')
    api_hash = Settings.get('api_hash', '')
    phone = Settings.get('phone', '')
    if not all([api_id_str, api_hash, phone]):
        return jsonify({'ok': False, 'message': 'لطفاً API ID، API Hash و شماره تلفن را ذخیره کنید'})
    try:
        result = run_async(start_client(int(api_id_str), api_hash, phone))
        return jsonify({'ok': True, **result})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/telegram/verify', methods=['POST'])
@login_required
def telegram_verify():
    from bot.telegram_reader import verify_code, run_async
    code = request.form.get('code', '').strip()
    password = request.form.get('password', '').strip()
    phone = Settings.get('phone', '')
    if not code:
        return jsonify({'ok': False, 'message': 'کد را وارد کنید'})
    try:
        result = run_async(verify_code(phone, code, password or None))
        if result.get('status') == 'authorized':
            return jsonify({'ok': True, 'message': 'اتصال به تلگرام برقرار شد'})
        elif result.get('status') == 'need_password':
            return jsonify({'ok': False, 'need_password': True, 'message': 'رمز دو مرحله‌ای نیاز است'})
        return jsonify({'ok': False, 'message': result.get('message', 'خطا')})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/telegram/test-bot', methods=['POST'])
@login_required
def telegram_test_bot():
    from bot.telegram_sender import test_bot_token
    token = Settings.get('bot_token', '')
    if not token:
        return jsonify({'ok': False, 'message': 'توکن ربات وارد نشده'})
    result = test_bot_token(token)
    if result.get('ok'):
        return jsonify({'ok': True, 'message': f'ربات @{result["username"]} متصل شد'})
    return jsonify({'ok': False, 'message': result.get('error', 'خطا')})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
