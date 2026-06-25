import re


def parse_source_prices(text: str) -> dict:
    """
    Parse buy/sell prices from source channel messages.
    Expected formats:
      💰#تتر[USDT] 168,100فروش♦️
      💰#تتر[USDT] 168,111خرید🔹
    Returns dict with 'buy', 'sell', or None values.
    """
    result = {'buy': None, 'sell': None}
    if not text:
        return result

    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        price = _extract_number(line)
        if price is None:
            continue
        if 'خرید' in line or 'buy' in line.lower():
            result['buy'] = price
        elif 'فروش' in line or 'sell' in line.lower():
            result['sell'] = price

    return result


def parse_dest_price(text: str) -> float | None:
    """
    Parse price from destination channel message.
    Expected format: قیمت تتر : 167500 تومان 💵 USDT
    """
    if not text:
        return None
    return _extract_number(text)


def _extract_number(text: str) -> float | None:
    # Remove commas then find the first number
    cleaned = text.replace(',', '').replace('٬', '')
    match = re.search(r'\b(\d{4,})\b', cleaned)
    if match:
        return float(match.group(1))
    return None


def calculate_average(buy: float | None, sell: float | None) -> float | None:
    if buy is not None and sell is not None:
        return (buy + sell) / 2
    if buy is not None:
        return buy
    if sell is not None:
        return sell
    return None
