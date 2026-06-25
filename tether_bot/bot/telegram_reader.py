import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

logger = logging.getLogger(__name__)

_client: TelegramClient | None = None
_session_file = 'tether_session'


def get_client(api_id: int, api_hash: str) -> TelegramClient:
    global _client
    if _client is None:
        _client = TelegramClient(_session_file, api_id, api_hash)
    return _client


async def fetch_latest_messages(api_id: int, api_hash: str, channel: str, limit: int = 5) -> list[str]:
    """Fetch the latest messages from a public Telegram channel."""
    client = get_client(api_id, api_hash)
    try:
        if not client.is_connected():
            await client.connect()
        if not await client.is_user_authorized():
            logger.warning("Telethon client not authorized")
            return []
        messages = []
        async for msg in client.iter_messages(channel, limit=limit):
            if msg.text:
                messages.append(msg.text)
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages from {channel}: {e}")
        return []


async def start_client(api_id: int, api_hash: str, phone: str) -> dict:
    """Start Telethon client and initiate login."""
    global _client
    _client = TelegramClient(_session_file, api_id, api_hash)
    await _client.connect()

    if await _client.is_user_authorized():
        return {'status': 'already_authorized'}

    await _client.send_code_request(phone)
    return {'status': 'code_sent', 'phone': phone}


async def verify_code(phone: str, code: str, password: str = None) -> dict:
    """Verify the OTP code sent to phone."""
    global _client
    if _client is None:
        return {'status': 'error', 'message': 'Client not started'}
    try:
        await _client.sign_in(phone, code)
        return {'status': 'authorized'}
    except SessionPasswordNeededError:
        if password:
            await _client.sign_in(password=password)
            return {'status': 'authorized'}
        return {'status': 'need_password'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


async def disconnect_client():
    global _client
    if _client and _client.is_connected():
        await _client.disconnect()


def run_async(coro):
    """Run async coroutine in a new event loop (for use from sync Flask context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
