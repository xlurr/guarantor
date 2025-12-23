-- Создание таблицы users
CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    reg_date TIMESTAMPTZ DEFAULT now(),
    wallet_ton VARCHAR(255),
    wallet_btc VARCHAR(255),
    total_deals INT DEFAULT 0,
    success_rate NUMERIC(5,2) DEFAULT 0 CHECK (success_rate >= 0 AND success_rate <= 100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user'))
);

-- Создание таблицы deals
CREATE TABLE IF NOT EXISTS deals (
    deal_id BIGSERIAL PRIMARY KEY,
    buyer_id BIGINT NOT NULL,
    seller_id BIGINT NOT NULL,
    amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    date_created TIMESTAMPTZ DEFAULT now(),
    status VARCHAR(50) DEFAULT 'awaiting_confirmation',
    commission NUMERIC(10,2) DEFAULT 0,
    buyer_confirm BOOLEAN DEFAULT false,
    seller_confirm BOOLEAN DEFAULT false,
    currency VARCHAR(10),
    payment_status VARCHAR(50) DEFAULT 'pending',
    expiry_time TIMESTAMPTZ,
    garant_payment_address VARCHAR(255),
    creation_confirmed BOOLEAN DEFAULT false,
    CONSTRAINT fk_buyer FOREIGN KEY (buyer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_seller FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_different_users CHECK (buyer_id != seller_id),
    CONSTRAINT deals_currency_check CHECK (currency IN ('TON', 'BTC')),
    CONSTRAINT deals_payment_status_check CHECK (payment_status IN ('pending', 'paid', 'confirmed')),
    CONSTRAINT deals_status_check CHECK (status IN ('awaiting_confirmation', 'awaiting_payment', 'payment_received', 'awaiting_delivery', 'completed', 'cancelled', 'expired'))
);

-- Создание таблицы transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL,
    amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) DEFAULT 'USDT',
    garant_wallet VARCHAR(255) NOT NULL,
    receiver_wallet VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    date TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT fk_deal FOREIGN KEY (deal_id) REFERENCES deals(deal_id) ON DELETE CASCADE
);

-- Создание таблицы event_log
CREATE TABLE IF NOT EXISTS event_log (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT now(),
    initiator_id BIGINT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    CONSTRAINT fk_initiator FOREIGN KEY (initiator_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Создание таблицы admins
CREATE TABLE IF NOT EXISTS admins (
    admin_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    access_rights VARCHAR(100) DEFAULT 'users:r,deals:r',
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Индексы для deals
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id);
CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id);
CREATE INDEX IF NOT EXISTS idx_deals_date ON deals(date_created DESC);

-- Индексы для transactions
CREATE INDEX IF NOT EXISTS idx_transactions_deal ON transactions(deal_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date DESC);

-- Индексы для event_log
CREATE INDEX IF NOT EXISTS idx_eventlog_initiator ON event_log(initiator_id);
CREATE INDEX IF NOT EXISTS idx_eventlog_action ON event_log(action);
CREATE INDEX IF NOT EXISTS idx_eventlog_timestamp ON event_log(timestamp DESC);

-- Индекс для admins
CREATE INDEX IF NOT EXISTS idx_admins_login ON admins(login);

-- Тестовые данные
INSERT INTO users (telegram_id, username, wallet_ton, wallet_btc, role) VALUES
(123456789, 'test_buyer', NULL, 'bc1qtest...buyer', 'user'),
(987654321, 'test_seller', 'UQTest...seller', 'bc1qtest...seller', 'user'),
(111222333, 'admin_user', NULL, NULL, 'admin')
ON CONFLICT (telegram_id) DO NOTHING;
