import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Создает подключение к БД"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# === USERS ===

def get_or_create_user(telegram_id: int, username: str, full_name: str):
    """Получить или создать пользователя (защита от инъекций через %s)"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_id = %s",
                (telegram_id,)
            )
            user = cur.fetchone()
            
            if not user:
                cur.execute(
                    """INSERT INTO users (telegram_id, username, role) 
                       VALUES (%s, %s, 'user') RETURNING *""",
                    (telegram_id, username)
                )
                user = cur.fetchone()
                conn.commit()
                
                log_event(user['user_id'], 'user_registered', 
                         f'{{"telegram_id": {telegram_id}}}')
            
            return user
    finally:
        conn.close()

def update_wallet(user_id: int, currency: str, wallet_address: str):
    """Обновить кошелёк пользователя"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            column = 'wallet_ton' if currency == 'TON' else 'wallet_btc'
            cur.execute(
                f"UPDATE users SET {column} = %s WHERE user_id = %s",
                (wallet_address, user_id)
            )
            conn.commit()
            log_event(user_id, 'wallet_updated', 
                     f'{{"currency": "{currency}", "wallet": "{wallet_address}"}}')
    finally:
        conn.close()

def get_user_by_id(user_id: int):
    """Получить пользователя по user_id"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()

# === DEALS ===

def create_deal(buyer_id: int, seller_id: int, amount: float, currency: str, 
                garant_address: str, expiry_time):
    """Создать сделку"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            commission = amount * 0.01
            cur.execute(
                """INSERT INTO deals 
                   (buyer_id, seller_id, amount, currency, garant_payment_address, 
                    expiry_time, commission, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'awaiting_confirmation') 
                   RETURNING deal_id""",
                (buyer_id, seller_id, amount, currency, garant_address, 
                 expiry_time, commission)
            )
            deal_id = cur.fetchone()['deal_id']
            conn.commit()
            
            log_event(buyer_id, 'deal_created', 
                     f'{{"deal_id": {deal_id}, "amount": {amount}, "currency": "{currency}"}}')
            return deal_id
        
    finally:
        conn.close()

def confirm_deal_creation(deal_id: int, user_id: int):
    """Продавец подтверждает создание сделки"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE deals 
                   SET creation_confirmed = true, status = 'awaiting_payment' 
                   WHERE deal_id = %s""",
                (deal_id,)
            )
            conn.commit()
            log_event(user_id, 'deal_confirmed', f'{{"deal_id": {deal_id}}}')
    finally:
        conn.close()

def cancel_deal(deal_id: int, user_id: int):
    """Отменить сделку"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE deals SET status = %s WHERE deal_id = %s",
                ('cancelled', deal_id)
            )
            conn.commit()
            log_event(user_id, 'deal_cancelled', f'{{"deal_id": {deal_id}}}')
    finally:
        conn.close()

def confirm_payment(deal_id: int):
    """Покупатель оплатил"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE deals 
                   SET payment_status = 'paid', status = 'payment_received' 
                   WHERE deal_id = %s""",
                (deal_id,)
            )
            conn.commit()
    finally:
        conn.close()

def confirm_delivery(deal_id: int, user_id: int, is_buyer: bool):
    """Подтверждение получения товара"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            column = 'buyer_confirm' if is_buyer else 'seller_confirm'
            cur.execute(
                f"UPDATE deals SET {column} = true WHERE deal_id = %s",
                (deal_id,)
            )
            
            cur.execute(
                "SELECT buyer_confirm, seller_confirm FROM deals WHERE deal_id = %s",
                (deal_id,)
            )
            result = cur.fetchone()
            
            if result['buyer_confirm'] and result['seller_confirm']:
                cur.execute(
                    """UPDATE deals 
                       SET status = 'completed', payment_status = 'confirmed' 
                       WHERE deal_id = %s""",
                    (deal_id,)
                )
                log_event(user_id, 'deal_completed', f'{{"deal_id": {deal_id}}}')
            
            conn.commit()
    finally:
        conn.close()

def get_user_deals(user_id: int, status_filter=None):
    """Получить сделки пользователя"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status_filter:
                cur.execute(
                    """SELECT d.*, 
                       CASE WHEN d.buyer_id = %s THEN 'buyer' ELSE 'seller' END as role
                       FROM deals d 
                       WHERE (d.buyer_id = %s OR d.seller_id = %s) 
                       AND d.status = %s
                       ORDER BY d.date_created DESC""",
                    (user_id, user_id, user_id, status_filter)
                )
            else:
                cur.execute(
                    """SELECT d.*, 
                       CASE WHEN d.buyer_id = %s THEN 'buyer' ELSE 'seller' END as role
                       FROM deals d 
                       WHERE d.buyer_id = %s OR d.seller_id = %s
                       ORDER BY d.date_created DESC""",
                    (user_id, user_id, user_id)
                )
            return cur.fetchall()
    finally:
        conn.close()

def get_deal_by_id(deal_id: int):
    """Получить сделку по ID"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM deals WHERE deal_id = %s", (deal_id,))
            return cur.fetchone()
    finally:
        conn.close()

def update_deal_status(deal_id: int, status: str):
    """Обновление статуса сделки"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE deals SET status = %s WHERE deal_id = %s",
                (status, deal_id)
            )
            conn.commit()
    finally:
        conn.close()

# === EVENT LOG ===

def log_event(user_id: int, action: str, details: str):
    """Записать событие в лог"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO event_log (initiator_id, action, details) VALUES (%s, %s, %s)",
                (user_id, action, details)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging event: {e}")
    finally:
        conn.close()

# === SCHEDULER ===

def expire_old_deals():
    """Фоновая задача: отменять просроченные сделки"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE deals 
                   SET status = 'expired' 
                   WHERE status = 'awaiting_payment' 
                   AND expiry_time < NOW()
                   RETURNING deal_id"""
            )
            expired = cur.fetchall()
            conn.commit()
            
            for deal in expired:
                logger.info(f"Deal {deal['deal_id']} expired")
    finally:
        conn.close()

# === FOR ADMIN ===

def get_all_users():
    """Получить всех пользователей"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY user_id DESC")
            users = cur.fetchall()
            return users
    finally:
        conn.close()

def get_all_deals():
    """Получить все сделки"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.*, 
                       b.username as buyer_username, 
                       s.username as seller_username
                FROM deals d
                LEFT JOIN users b ON d.buyer_id = b.user_id
                LEFT JOIN users s ON d.seller_id = s.user_id
                ORDER BY d.deal_id DESC
            """)
            deals = cur.fetchall()
            return deals
    finally:
        conn.close()

def get_system_stats():
    """Получить статистику системы"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Количество пользователей
            cur.execute("SELECT COUNT(*) as count FROM users")
            total_users = cur.fetchone()['count']
            
            # Количество сделок
            cur.execute("SELECT COUNT(*) as count FROM deals")
            total_deals = cur.fetchone()['count']
            
            # Завершённые сделки
            cur.execute("SELECT COUNT(*) as count FROM deals WHERE status = 'completed'")
            completed_deals = cur.fetchone()['count']
            
            # Активные сделки
            cur.execute("SELECT COUNT(*) as count FROM deals WHERE status IN ('awaiting_confirmation', 'awaiting_payment', 'awaiting_admin_confirmation', 'payment_received')")
            active_deals = cur.fetchone()['count']
            
            # Общий объём
            cur.execute("SELECT SUM(amount) as total FROM deals WHERE status = 'completed'")
            result = cur.fetchone()['total']
            total_volume = result if result else 0
            
            return {
                'total_users': total_users,
                'total_deals': total_deals,
                'completed_deals': completed_deals,
                'active_deals': active_deals,
                'total_volume': total_volume
            }
    finally:
        conn.close()

def force_cancel_deal(deal_id: int):
    """Принудительная отмена сделки админом"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE deals SET status = %s WHERE deal_id = %s",
                ('cancelled', deal_id)
            )
            conn.commit()
    finally:
        conn.close()
