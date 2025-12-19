from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Мои сделки", callback_data="my_deals")],
        [InlineKeyboardButton(text="➕ Создать сделку", callback_data="create_deal")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💳 Управление кошельками", callback_data="wallets")],
    ])

def deal_type_choice():
    """Выбор роли в сделке"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Я покупатель", callback_data="deal_role:buyer")],
        [InlineKeyboardButton(text="💰 Я продавец", callback_data="deal_role:seller")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_main")],
    ])

def currency_choice():
    """Выбор валюты"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 TON", callback_data="currency:TON")],
        [InlineKeyboardButton(text="₿ BTC", callback_data="currency:BTC")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_main")],
    ])

def confirm_deal_creation(deal_id: int):
    """Продавцу: подтвердить создание сделки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_creation:{deal_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_creation:{deal_id}")],
    ])

def deal_actions(deal_id: int, role: str, status: str):
    """Действия со сделкой"""
    buttons = []
    
    if status == 'payment_received' or status == 'awaiting_delivery':
        buttons.append([InlineKeyboardButton(
            text="✅ Подтвердить получение", 
            callback_data=f"confirm_delivery:{deal_id}"
        )])
    
    if status in ['awaiting_confirmation', 'awaiting_payment']:
        buttons.append([InlineKeyboardButton(
            text="❌ Отменить сделку", 
            callback_data=f"cancel_deal:{deal_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="« Назад к сделкам", callback_data="my_deals")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_id_button():
    """Кнопка для получения своего ID"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆔 Получить мой ID", callback_data="get_my_id")],
    ])

def payment_confirmation_keyboard(deal_id: int):
    """Кнопка 'Я перевёл деньги' для покупателя"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Я перевёл деньги", callback_data=f"payment_sent:{deal_id}")],
        [InlineKeyboardButton(text="❌ Отменить сделку", callback_data=f"cancel_deal:{deal_id}")]
    ])

def admin_confirmation_keyboard(deal_id: int):
    """Кнопки подтверждения/отклонения для админа"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить перевод", callback_data=f"admin_confirm:{deal_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject:{deal_id}")]
    ])

def buyer_confirm_delivery_keyboard(deal_id: int):
    """Кнопка подтверждения получения товара для покупателя"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить получение товара", callback_data=f"confirm_received:{deal_id}")]
    ])
