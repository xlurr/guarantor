from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import currency_choice, main_menu
from database import get_or_create_user, update_wallet
from states import WalletManagement

router = Router()

@router.callback_query(F.data == "wallets")
async def manage_wallets_callback(callback: CallbackQuery):
    user = get_or_create_user(callback.from_user.id, callback.from_user.username or "Без username", callback.from_user.full_name)
    text = f"💳 **Ваши кошельки:**\n\n"
    text += f"💎 TON: `{user['wallet_ton'] or 'Не указан'}`\n"
    text += f"₿ BTC: `{user['wallet_btc'] or 'Не указан'}`\n\n"
    text += "Выберите валюту для добавления/изменения кошелька:"
    await callback.message.edit_text(text, reply_markup=currency_choice(), parse_mode="Markdown")
    await callback.answer()

async def manage_wallets(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username or "Без username", message.from_user.full_name)
    text = f"💳 **Ваши кошельки:**\n\n"
    text += f"💎 TON: `{user['wallet_ton'] or 'Не указан'}`\n"
    text += f"₿ BTC: `{user['wallet_btc'] or 'Не указан'}`\n\n"
    text += "Выберите валюту для добавления/изменения кошелька:"
    await message.answer(text, reply_markup=currency_choice(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("currency:"))
async def choose_wallet_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    await state.update_data(wallet_currency=currency)
    await state.set_state(WalletManagement.waiting_for_wallet_address)
    await callback.message.edit_text(f"Введите адрес кошелька {currency}:\n\nПример для TON: `UQD...ABC123`\nПример для BTC: `bc1q...xyz789`", parse_mode="Markdown")
    await callback.answer()

@router.message(WalletManagement.waiting_for_wallet_address)
async def save_wallet_address(message: Message, state: FSMContext):
    wallet_address = message.text.strip()
    data = await state.get_data()
    currency = data['wallet_currency']
    if len(wallet_address) < 20:
        await message.answer("❌ Адрес кошелька слишком короткий. Попробуйте ещё раз:")
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username or "Без username", message.from_user.full_name)
    update_wallet(user['user_id'], currency, wallet_address)
    await message.answer(f"✅ Кошелёк {currency} успешно добавлен!\n\nАдрес: `{wallet_address}`", parse_mode="Markdown")
    await state.clear()
