from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.inline import main_menu
from database import get_or_create_user, get_user_deals

router = Router()

@router.callback_query(F.data == "profile")
async def show_profile_callback(callback: CallbackQuery):
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    deals = get_user_deals(user['user_id'])
    active_deals = [d for d in deals if d['status'] in ['awaiting_confirmation', 'awaiting_payment', 'payment_received']]
    completed_deals = [d for d in deals if d['status'] == 'completed']
    text = f"""
👤 **Ваш профиль**

🆔 ID: `{user['user_id']}`
📱 Telegram: @{user['username']}
📅 Регистрация: {user['reg_date'].strftime('%d.%m.%Y')}
👔 Роль: {'Администратор' if user['role'] == 'admin' else 'Пользователь'}

📊 **Статистика:**
💼 Всего сделок: {user['total_deals']}
✅ Завершено: {len(completed_deals)}
⏳ Активных: {len(active_deals)}
⭐ Рейтинг успеха: {user['success_rate']}%

💳 **Кошельки:**
💎 TON: `{user['wallet_ton'] or 'Не указан'}`
₿ BTC: `{user['wallet_btc'] or 'Не указан'}`
"""
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()

async def show_profile(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username or "Без username", message.from_user.full_name)
    deals = get_user_deals(user['user_id'])
    active_deals = [d for d in deals if d['status'] in ['awaiting_confirmation', 'awaiting_payment', 'payment_received']]
    completed_deals = [d for d in deals if d['status'] == 'completed']
    text = f"""
👤 **Ваш профиль**

🆔 ID: `{user['user_id']}`
📱 Telegram: @{user['username']}
📅 Регистрация: {user['reg_date'].strftime('%d.%m.%Y')}
👔 Роль: {'Администратор' if user['role'] == 'admin' else 'Пользователь'}

📊 **Статистика:**
💼 Всего сделок: {user['total_deals']}
✅ Завершено: {len(completed_deals)}
⏳ Активных: {len(active_deals)}
⭐ Рейтинг успеха: {user['success_rate']}%

💳 **Кошельки:**
💎 TON: `{user['wallet_ton'] or 'Не указан'}`
₿ BTC: `{user['wallet_btc'] or 'Не указан'}`
"""
    await message.answer(text, parse_mode="Markdown")
