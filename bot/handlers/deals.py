from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from keyboards.inline import deal_type_choice, currency_choice, confirm_deal_creation, deal_actions, main_menu
from database import (get_or_create_user, get_user_by_id, create_deal, 
    confirm_deal_creation as db_confirm_creation, cancel_deal, 
    confirm_delivery, get_user_deals, get_deal_by_id, update_deal_status)
from states import DealCreation
from config import DEAL_EXPIRY_HOURS, ADMIN_ID
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "create_deal")
async def start_deal_creation_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Кто вы в этой сделке?", reply_markup=deal_type_choice())
    await state.set_state(DealCreation.waiting_for_role)
    await callback.answer()

async def start_deal_creation(message: Message, state: FSMContext):
    await message.answer("Кто вы в этой сделке?", reply_markup=deal_type_choice())
    await state.set_state(DealCreation.waiting_for_role)

@router.callback_query(F.data.startswith("deal_role:"), DealCreation.waiting_for_role)
async def choose_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await state.update_data(role=role)
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    role_text = "покупателем" if role == "buyer" else "продавцом"
    await callback.message.edit_text(f"Вы выбрали: {role_text}\n\nВаш ID: `{user['user_id']}`\n\nВведите ID второго участника сделки:", parse_mode="Markdown")
    await state.set_state(DealCreation.waiting_for_partner_id)
    await callback.answer()

@router.message(DealCreation.waiting_for_partner_id)
async def enter_partner_id(message: Message, state: FSMContext):
    try:
        partner_id = int(message.text)
    except ValueError:
        await message.answer("❌ ID должен быть числом. Попробуйте ещё раз:")
        return
    partner = get_user_by_id(partner_id)
    if not partner:
        await message.answer("❌ Пользователь с таким ID не найден.")
        return
    current_user = get_or_create_user(message.from_user.id, message.from_user.username or "Без username", message.from_user.full_name)
    if partner_id == current_user['user_id']:
        await message.answer("❌ Нельзя создать сделку с самим собой!")
        return
    await state.update_data(partner_id=partner_id, partner_username=partner['username'])
    await message.answer(f"✅ Партнёр найден: @{partner['username']}\n\nВведите сумму сделки:")
    await state.set_state(DealCreation.waiting_for_amount)

@router.message(DealCreation.waiting_for_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную сумму:")
        return
    await state.update_data(amount=amount)
    await message.answer(f"💰 Сумма: {amount}\n\nВыберите валюту:", reply_markup=currency_choice())
    await state.set_state(DealCreation.waiting_for_currency)

@router.callback_query(F.data.startswith("currency:"), DealCreation.waiting_for_currency)
async def choose_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    data = await state.get_data()
    current_user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    role = data['role']
    partner_id = data['partner_id']
    amount = data['amount']
    if role == 'seller':
        wallet_field = 'wallet_ton' if currency == 'TON' else 'wallet_btc'
        if not current_user[wallet_field]:
            await callback.message.edit_text(f"❌ Перед созданием сделки внесите ваши платежные данные для {currency}.\n\nПерейдите в раздел 💳 Кошельки", reply_markup=main_menu())
            await state.clear()
            await callback.answer()
            return
    buyer_id = current_user['user_id'] if role == 'buyer' else partner_id
    seller_id = current_user['user_id'] if role == 'seller' else partner_id
    garant_address = f"GARANT_{currency}_{datetime.now().timestamp()}"
    expiry_time = datetime.now() + timedelta(hours=DEAL_EXPIRY_HOURS)
    deal_id = create_deal(buyer_id, seller_id, amount, currency, garant_address, expiry_time)
    await callback.message.edit_text(f"✅ Сделка #{deal_id} создана!\n\n💰 Сумма: {amount} {currency}\n👤 Партнёр: @{data['partner_username']}\n\nОжидайте подтверждения от второго участника...")
    try:
        partner = get_user_by_id(partner_id)
        await callback.bot.send_message(chat_id=partner['telegram_id'], text=f"🔔 Новая сделка!\n\nПользователь @{callback.from_user.username} создал сделку:\n💰 Сумма: {amount} {currency}\n\nПодтвердите создание:", reply_markup=confirm_deal_creation(deal_id))
    except Exception as e:
        logger.error(f"Failed to notify partner: {e}")
    await state.clear()
    await callback.answer("Сделка создана!")

@router.callback_query(F.data.startswith("confirm_creation:"))
async def confirm_creation(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    db_confirm_creation(deal_id, user['user_id'])
    buyer = get_user_by_id(deal['buyer_id'])
    
    await callback.message.edit_text(f"✅ Вы подтвердили сделку #{deal_id}\n\nОжидайте оплату от покупателя...")
    
    # Добавляем кнопку "Я перевёл деньги"
    from keyboards.inline import payment_confirmation_keyboard
    
    await callback.bot.send_message(
        chat_id=buyer['telegram_id'], 
        text=(
            f"✅ Сделка #{deal_id} подтверждена!\n\n"
            f"💳 Переведите {deal['amount']} {deal['currency']} на адрес:\n"
            f"`{deal['garant_payment_address']}`\n\n"
            f"⏱ Таймер: {DEAL_EXPIRY_HOURS} часа\n\n"
            f"После перевода нажмите кнопку:"
        ),
        parse_mode="Markdown",
        reply_markup=payment_confirmation_keyboard(deal_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("reject_creation:"))
async def reject_creation(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    cancel_deal(deal_id, user['user_id'])
    await callback.message.edit_text(f"❌ Вы отклонили сделку #{deal_id}")
    buyer = get_user_by_id(deal['buyer_id'])
    await callback.bot.send_message(chat_id=buyer['telegram_id'], text=f"❌ Сделка #{deal_id} отклонена")
    await callback.answer()

@router.callback_query(F.data == "my_deals")
async def show_my_deals_callback(callback: CallbackQuery):
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    deals = get_user_deals(user['user_id'])
    if not deals:
        await callback.message.edit_text("У вас пока нет сделок", reply_markup=main_menu())
        await callback.answer()
        return
    
    status_names = {
        'awaiting_confirmation': 'Ожидает подтверждения',
        'awaiting_payment': 'Ожидает оплаты',
        'awaiting_admin_confirmation': 'Проверка админом',
        'payment_received': 'Оплата получена',
        'payment_rejected': 'Оплата отклонена',
        'completed': 'Завершена',
        'cancelled': 'Отменена',
        'expired': 'Истекла'
    }
    
    text = "💼 <b>Ваши сделки:</b>\n\n"
    for deal in deals[:10]:
        status_emoji = {
            'awaiting_confirmation': '⏳',
            'awaiting_payment': '💳',
            'awaiting_admin_confirmation': '🔍',
            'payment_received': '✅',
            'payment_rejected': '❌',
            'completed': '✅',
            'cancelled': '❌',
            'expired': '⏰'
        }.get(deal['status'], '❓')
        
        status_text = status_names.get(deal['status'], deal['status'])
        text += f"{status_emoji} Сделка #{deal['deal_id']}\n   💰 {deal['amount']} {deal['currency']}\n   Статус: {status_text}\n\n"
    
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")
    await callback.answer()

async def show_my_deals(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username or "Без username", message.from_user.full_name)
    deals = get_user_deals(user['user_id'])
    if not deals:
        await message.answer("У вас пока нет сделок")
        return
    
    status_names = {
        'awaiting_confirmation': 'Ожидает подтверждения',
        'awaiting_payment': 'Ожидает оплаты',
        'awaiting_admin_confirmation': 'Проверка админом',
        'payment_received': 'Оплата получена',
        'payment_rejected': 'Оплата отклонена',
        'completed': 'Завершена',
        'cancelled': 'Отменена',
        'expired': 'Истекла'
    }
    
    text = "💼 <b>Ваши сделки:</b>\n\n"
    for deal in deals[:10]:
        status_emoji = {
            'awaiting_confirmation': '⏳',
            'awaiting_payment': '💳',
            'awaiting_admin_confirmation': '🔍',
            'payment_received': '✅',
            'payment_rejected': '❌',
            'completed': '✅',
            'cancelled': '❌',
            'expired': '⏰'
        }.get(deal['status'], '❓')
        
        status_text = status_names.get(deal['status'], deal['status'])
        text += f"{status_emoji} Сделка #{deal['deal_id']}\n   💰 {deal['amount']} {deal['currency']}\n   Статус: {status_text}\n\n"
    
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("confirm_delivery:"))
async def confirm_delivery_callback(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    is_buyer = (user['user_id'] == deal['buyer_id'])
    confirm_delivery(deal_id, user['user_id'], is_buyer)
    deal = get_deal_by_id(deal_id)
    if deal['status'] == 'completed':
        await callback.message.edit_text(f"🎉 Сделка #{deal_id} завершена!\n\nДеньги переведены продавцу.")
        other_id = deal['seller_id'] if is_buyer else deal['buyer_id']
        other_user = get_user_by_id(other_id)
        await callback.bot.send_message(chat_id=other_user['telegram_id'], text=f"🎉 Сделка #{deal_id} завершена!")
    else:
        await callback.message.edit_text(f"✅ Вы подтвердили получение по сделке #{deal_id}\n\nОжидаем подтверждения от второго участника...")
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_deal:"))
async def cancel_deal_callback(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    cancel_deal(deal_id, user['user_id'])
    await callback.message.edit_text(f"❌ Сделка #{deal_id} отменена")
    await callback.answer()

# Обработчик: покупатель нажал "Я перевёл деньги"
@router.callback_query(F.data.startswith("payment_sent:"))
async def payment_sent(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = get_deal_by_id(deal_id)
    
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return
    
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    
    if user['user_id'] != deal['buyer_id']:
        await callback.answer("Только покупатель может подтвердить оплату", show_alert=True)
        return
    
    # Обновляем статус в БД
    update_deal_status(deal_id, 'awaiting_admin_confirmation')
    
    # Отправляем админу
    from keyboards.inline import admin_confirmation_keyboard
    
    buyer = get_user_by_id(deal['buyer_id'])
    seller = get_user_by_id(deal['seller_id'])
    
    try:
        await callback.bot.send_message(
            chat_id=ADMIN_ID,  # 757042486
            text=(
                f"💰 <b>Подтверждение перевода</b>\n\n"
                f"🔢 Сделка: #{deal_id}\n"
                f"💵 Сумма: {deal['amount']} {deal['currency']}\n"
                f"👤 Покупатель: @{buyer['username']} (ID: {buyer['user_id']})\n"
                f"👤 Продавец: @{seller['username']} (ID: {seller['user_id']})\n"
                f"📍 Адрес: <code>{deal['garant_payment_address']}</code>\n\n"
                f"Проверьте поступление средств и подтвердите:"
            ),
            parse_mode="HTML",
            reply_markup=admin_confirmation_keyboard(deal_id)
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    await callback.message.edit_text(
        f"✅ Заявка отправлена администратору\n\n"
        f"Сделка: #{deal_id}\n"
        f"Сумма: {deal['amount']} {deal['currency']}\n\n"
        f"⏳ Ожидайте проверки перевода..."
    )
    await callback.answer("Заявка отправлена на проверку")
