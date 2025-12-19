from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext  # ДОБАВЬ ЭТУ СТРОКУ
from keyboards.inline import main_menu, get_user_id_button
from keyboards.reply import main_reply_keyboard
from database import get_or_create_user

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка /start"""
    user = get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "Без username",
        full_name=message.from_user.full_name
    )
    
    welcome_text = f"""
👋 Добро пожаловать, {message.from_user.first_name}!

Я бот-гарант для безопасных сделок с криптовалютой.

🔐 Как это работает:
1. Создаёте сделку с другим пользователем
2. Покупатель переводит деньги на счёт гаранта
3. Продавец передаёт товар/услугу
4. Оба подтверждают сделку → деньги уходят продавцу

💼 Ваш ID: `{user['user_id']}`
Отправьте его партнёру для создания сделки.
"""
    
    await message.answer(
        welcome_text,
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "get_my_id")
async def get_my_id(callback: CallbackQuery):
    """Получить свой ID"""
    user = get_or_create_user(
        callback.from_user.id,
        callback.from_user.username or "Без username",
        callback.from_user.full_name
    )
    
    await callback.answer(
        f"Ваш ID: {user['user_id']}",
        show_alert=True
    )

@router.message(F.text == "👤 Профиль")
async def profile_text(message: Message):
    """Профиль через reply-кнопку"""
    from handlers.profile import show_profile
    await show_profile(message)

@router.message(F.text == "💼 Мои сделки")
async def deals_text(message: Message):
    """Сделки через reply-кнопку"""
    from handlers.deals import show_my_deals
    await show_my_deals(message)

@router.message(F.text == "➕ Создать сделку")
async def create_deal_text(message: Message, state: FSMContext):
    """Создать сделку через reply-кнопку"""
    from handlers.deals import start_deal_creation
    await start_deal_creation(message, state)

@router.message(F.text == "💳 Кошельки")
async def wallets_text(message: Message):
    """Кошельки через reply-кнопку"""
    from handlers.wallet import manage_wallets
    await manage_wallets(message)
