import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Telegram ID для админ-доступа
ADMIN_ID = 757042486

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'garant_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'admin123')
}

# Crypto API
TON_API_KEY = os.getenv('TON_API_KEY')
BTC_API_KEY = os.getenv('BTC_API_KEY')

# Таймауты
DEAL_EXPIRY_HOURS = 2


