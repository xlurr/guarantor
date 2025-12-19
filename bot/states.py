from aiogram.fsm.state import State, StatesGroup

class DealCreation(StatesGroup):
    """Состояния создания сделки"""
    waiting_for_role = State()
    waiting_for_partner_id = State()
    waiting_for_amount = State()
    waiting_for_currency = State()

class WalletManagement(StatesGroup):
    """Управление кошельками"""
    waiting_for_currency_choice = State()
    waiting_for_wallet_address = State()
