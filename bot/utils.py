import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    """Хеширование пароля (для админов)"""
    return hashlib.sha256(password.encode()).hexdigest()

def format_datetime(dt: datetime) -> str:
    """Форматирование даты"""
    return dt.strftime('%d.%m.%Y %H:%M')

def generate_garant_address(currency: str, deal_id: int) -> str:
    """Генерация адреса гаранта для оплаты"""
    timestamp = datetime.now().timestamp()
    return f"GARANT_{currency}_{deal_id}_{timestamp}"

def validate_wallet_address(address: str, currency: str) -> bool:
    """Валидация адреса кошелька"""
    if currency == 'TON':
        return address.startswith('UQ') and len(address) > 40
    elif currency == 'BTC':
        return address.startswith('bc1') and len(address) > 40
    return False
