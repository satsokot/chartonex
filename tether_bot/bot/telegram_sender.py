import logging
import requests

logger = logging.getLogger(__name__)


def send_price_message(
    bot_token: str,
    channel: str,
    text: str,
    button1_text: str = None,
    button1_url: str = None,
    button2_text: str = None,
    button2_url: str = None,
    edit_message_id: int = None,
) -> dict:
    """Send or edit a price message with glass inline buttons."""
    inline_keyboard = _build_keyboard(button1_text, button1_url, button2_text, button2_url)

    payload = {
        'chat_id': channel,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': {'inline_keyboard': inline_keyboard} if inline_keyboard else None,
    }

    base_url = f'https://api.telegram.org/bot{bot_token}'

    if edit_message_id:
        url = f'{base_url}/editMessageText'
        payload['message_id'] = edit_message_id
    else:
        url = f'{base_url}/sendMessage'

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get('ok'):
            msg_id = data['result'].get('message_id')
            logger.info(f"Message sent/edited successfully. message_id={msg_id}")
            return {'ok': True, 'message_id': msg_id}
        else:
            logger.error(f"Telegram API error: {data}")
            # If editing fails (message not found), send a new one
            if edit_message_id and data.get('error_code') in (400, 404):
                return send_price_message(
                    bot_token, channel, text,
                    button1_text, button1_url,
                    button2_text, button2_url,
                    edit_message_id=None
                )
            return {'ok': False, 'error': data.get('description', 'Unknown error')}
    except Exception as e:
        logger.error(f"Exception sending message: {e}")
        return {'ok': False, 'error': str(e)}


def _build_keyboard(b1_text, b1_url, b2_text, b2_url):
    buttons = []
    if b1_text and b1_url:
        buttons.append({'text': b1_text, 'url': b1_url})
    if b2_text and b2_url:
        buttons.append({'text': b2_text, 'url': b2_url})
    if not buttons:
        return []
    return [buttons]


def test_bot_token(bot_token: str) -> dict:
    """Verify bot token is valid."""
    try:
        resp = requests.get(
            f'https://api.telegram.org/bot{bot_token}/getMe',
            timeout=10
        )
        data = resp.json()
        if data.get('ok'):
            return {'ok': True, 'username': data['result'].get('username')}
        return {'ok': False, 'error': data.get('description')}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
