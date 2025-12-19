from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import (get_deal_by_id, update_deal_status, get_user_by_id, 
                     get_all_users, get_all_deals, get_system_stats, force_cancel_deal)
from config import ADMIN_ID
import logging

router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверка админа"""
    return user_id == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin - главная админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    stats = get_system_stats()
    
    text = (
        f"🔧 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика системы:</b>\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"💼 Всего сделок: {stats['total_deals']}\n"
        f"✅ Завершено: {stats['completed_deals']}\n"
        f"⏳ Активных: {stats['active_deals']}\n"
        f"💰 Общий объём: {stats['total_volume']:.2f}\n\n"
        f"<b>Доступные команды:</b>\n"
        f"/users - Список пользователей\n"
        f"/deals - Список сделок\n"
        f"/active_deals - Активные сделки\n"
        f"/stats - Детальная статистика"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("users"))
async def cmd_users(message: Message):
    """Список всех пользователей"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    users = get_all_users()
    
    if not users:
        await message.answer("❌ Пользователей нет")
        return
    
    text = f"👥 <b>Список пользователей ({len(users)}):</b>\n\n"
    
    for user in users[:50]:  # Показываем первых 50
        username = user['username'] if user['username'] else 'Без username'
        text += (
            f"🆔 ID: {user['user_id']}\n"
            f"👤 Username: @{username}\n"
            f"🔗 TG ID: <code>{user['telegram_id']}</code>\n\n"
        )
    
    if len(users) > 50:
        text += f"\n... и ещё {len(users) - 50} пользователей"
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("deals"))
async def cmd_deals(message: Message):
    """Список всех сделок"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    deals = get_all_deals()
    
    if not deals:
        await message.answer("❌ Сделок нет")
        return
    
    status_emoji = {
        'awaiting_confirmation': '⏳',
        'awaiting_payment': '💳',
        'awaiting_admin_confirmation': '🔍',
        'payment_received': '✅',
        'payment_rejected': '❌',
        'completed': '✅',
        'cancelled': '❌',
        'expired': '⏰'
    }
    
    text = f"💼 <b>Все сделки ({len(deals)}):</b>\n\n"
    
    for deal in deals[:30]:  # Показываем первых 30
        emoji = status_emoji.get(deal['status'], '❓')
        buyer_username = deal['buyer_username'] if deal['buyer_username'] else 'Без username'
        seller_username = deal['seller_username'] if deal['seller_username'] else 'Без username'
        
        text += (
            f"{emoji} <b>Сделка #{deal['deal_id']}</b>\n"
            f"💵 Сумма: {deal['amount']} {deal['currency']}\n"
            f"👤 Покупатель: @{buyer_username}\n"
            f"👤 Продавец: @{seller_username}\n"
            f"📊 Статус: {deal['status']}\n\n"
        )
    
    if len(deals) > 30:
        text += f"\n... и ещё {len(deals) - 30} сделок"
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("active_deals"))
async def cmd_active_deals(message: Message):
    """Активные сделки с кнопками отмены"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    deals = get_all_deals()
    active_statuses = ['awaiting_confirmation', 'awaiting_payment', 'awaiting_admin_confirmation', 'payment_received']
    active_deals = [d for d in deals if d['status'] in active_statuses]
    
    if not active_deals:
        await message.answer("✅ Активных сделок нет")
        return
    
    status_emoji = {
        'awaiting_confirmation': '⏳',
        'awaiting_payment': '💳',
        'awaiting_admin_confirmation': '🔍',
        'payment_received': '✅'
    }
    
    text = f"⏳ <b>Активные сделки ({len(active_deals)}):</b>\n\n"
    
    for deal in active_deals:
        emoji = status_emoji.get(deal['status'], '❓')
        buyer_username = deal['buyer_username'] if deal['buyer_username'] else 'Без username'
        seller_username = deal['seller_username'] if deal['seller_username'] else 'Без username'
        
        text += (
            f"{emoji} <b>Сделка #{deal['deal_id']}</b>\n"
            f"💵 Сумма: {deal['amount']} {deal['currency']}\n"
            f"👤 Покупатель: @{buyer_username} (ID: {deal['buyer_id']})\n"
            f"👤 Продавец: @{seller_username} (ID: {deal['seller_id']})\n"
            f"📊 Статус: {deal['status']}\n"
            f"🗑 Отменить: /cancel_deal_{deal['deal_id']}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Детальная статистика"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    stats = get_system_stats()
    deals = get_all_deals()
    
    # Статистика по валютам
    ton_deals = len([d for d in deals if d['currency'] == 'TON' and d['status'] == 'completed'])
    btc_deals = len([d for d in deals if d['currency'] == 'BTC' and d['status'] == 'completed'])
    usdt_deals = len([d for d in deals if d['currency'] == 'USDT' and d['status'] == 'completed'])
    
    # Статистика по статусам
    cancelled = len([d for d in deals if d['status'] == 'cancelled'])
    expired = len([d for d in deals if d['status'] == 'expired'])
    
    text = (
        f"📊 <b>Детальная статистика</b>\n\n"
        f"👥 <b>Пользователи:</b> {stats['total_users']}\n\n"
        f"💼 <b>Сделки:</b>\n"
        f"  • Всего: {stats['total_deals']}\n"
        f"  • ✅ Завершено: {stats['completed_deals']}\n"
        f"  • ⏳ Активных: {stats['active_deals']}\n"
        f"  • ❌ Отменено: {cancelled}\n"
        f"  • ⏰ Истекло: {expired}\n\n"
        f"💰 <b>По валютам (завершённые):</b>\n"
        f"  • TON: {ton_deals}\n"
        f"  • BTC: {btc_deals}\n"
        f"  • USDT: {usdt_deals}\n\n"
        f"💵 <b>Общий объём:</b> {stats['total_volume']:.2f}"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text.startswith("/cancel_deal_"))
async def cmd_cancel_deal(message: Message):
    """Принудительная отмена сделки"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    try:
        deal_id = int(message.text.split("_")[-1])
    except ValueError:
        await message.answer("❌ Неверный формат команды")
        return
    
    deal = get_deal_by_id(deal_id)
    
    if not deal:
        await message.answer("❌ Сделка не найдена")
        return
    
    if deal['status'] in ['completed', 'cancelled', 'expired']:
        await message.answer(f"❌ Сделка #{deal_id} уже завершена/отменена")
        return
    
    # Отменяем сделку
    force_cancel_deal(deal_id)
    
    # Уведомляем участников
    buyer = get_user_by_id(deal['buyer_id'])
    seller = get_user_by_id(deal['seller_id'])
    
    notified = []
    
    try:
        await message.bot.send_message(
            buyer['telegram_id'],
            f"⚠️ <b>Сделка #{deal_id} отменена администратором</b>",
            parse_mode="HTML"
        )
        notified.append("покупатель")
    except Exception as e:
        logger.error(f"Failed to notify buyer: {e}")
    
    try:
        await message.bot.send_message(
            seller['telegram_id'],
            f"⚠️ <b>Сделка #{deal_id} отменена администратором</b>",
            parse_mode="HTML"
        )
        notified.append("продавец")
    except Exception as e:
        logger.error(f"Failed to notify seller: {e}")
    
    notification_status = f"Уведомлены: {', '.join(notified)}" if notified else "Участники не уведомлены"
    
    await message.answer(
        f"✅ <b>Сделка #{deal_id} отменена</b>\n\n"
        f"💵 Сумма: {deal['amount']} {deal['currency']}\n"
        f"📊 {notification_status}",
        parse_mode="HTML"
    )

# Обработчики подтверждения/отклонения переводов
@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm_payment(callback: CallbackQuery):
    """Админ подтверждает перевод"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    # Обновляем статус на "payment_received"
    update_deal_status(deal_id, 'payment_received')
    
    buyer = get_user_by_id(deal['buyer_id'])
    seller = get_user_by_id(deal['seller_id'])
    
    # НОВОЕ: Импортируем клавиатуру
    from keyboards.inline import buyer_confirm_delivery_keyboard
    
    # Уведомляем покупателя С КНОПКОЙ
    try:
        await callback.bot.send_message(
            chat_id=buyer['telegram_id'],
            text=(
                f"✅ <b>Перевод подтверждён!</b>\n\n"
                f"Сделка: #{deal_id}\n"
                f"Сумма: {deal['amount']} {deal['currency']}\n\n"
                f"Администратор проверил перевод.\n"
                f"Ожидайте отправки товара от продавца.\n\n"
                f"После получения товара нажмите кнопку ниже:"
            ),
            parse_mode="HTML",
            reply_markup=buyer_confirm_delivery_keyboard(deal_id)  # НОВАЯ КНОПКА
        )
    except Exception as e:
        logger.error(f"Failed to notify buyer: {e}")
    
    # Уведомляем продавца
    try:
        await callback.bot.send_message(
            chat_id=seller['telegram_id'],
            text=(
                f"✅ <b>Оплата получена!</b>\n\n"
                f"Сделка: #{deal_id}\n"
                f"Сумма: {deal['amount']} {deal['currency']}\n\n"
                f"Покупатель перевёл деньги (подтверждено администратором).\n"
                f"Отправьте товар покупателю."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify seller: {e}")
    
    await callback.answer("✅ Перевод подтверждён")
    await callback.message.edit_text(
        f"✅ <b>Сделка #{deal_id} подтверждена</b>\n\n"
        f"Сумма: {deal['amount']} {deal['currency']}\n"
        f"Статус: Оплата получена",
        parse_mode="HTML"
    )
    
    logger.info(f"Admin {callback.from_user.id} confirmed deal {deal_id}")


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject_payment(callback: CallbackQuery):
    """Админ отклоняет перевод"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    # Обновляем статус
    update_deal_status(deal_id, 'payment_rejected')
    
    buyer = get_user_by_id(deal['buyer_id'])
    
    # Уведомляем покупателя
    try:
        await callback.bot.send_message(
            chat_id=buyer['telegram_id'],
            text=(
                f"❌ <b>Перевод отклонён</b>\n\n"
                f"Сделка: #{deal_id}\n"
                f"Сумма: {deal['amount']} {deal['currency']}\n\n"
                f"Администратор не подтвердил перевод.\n"
                f"Свяжитесь с поддержкой."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify buyer: {e}")
    
    await callback.answer("❌ Перевод отклонён")
    await callback.message.edit_text(
        f"❌ <b>Сделка #{deal_id} отклонена</b>\n\n"
        f"Сумма: {deal['amount']} {deal['currency']}\n"
        f"Статус: Отклонена",
        parse_mode="HTML"
    )
    
    logger.info(f"Admin {callback.from_user.id} rejected deal {deal_id}")
