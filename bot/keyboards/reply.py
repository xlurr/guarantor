from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_reply_keyboard():
    """Главная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💼 Мои сделки"), KeyboardButton(text="➕ Создать сделку")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💳 Кошельки")],
        ],
        resize_keyboard=True
    )
