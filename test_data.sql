-- test_data.sql

-- Тестовые пользователи
INSERT INTO users (telegram_id, username, wallet_ton, wallet_btc, role) VALUES
(123456789, 'buyer_ivan', NULL, 'bc1qtest123buyer', 'user'),
(987654321, 'seller_alex', 'UQTest456seller', 'bc1qtest456seller', 'user'),
(555555555, 'trader_maria', 'UQTest789trader', NULL, 'user'),
(111111111, 'admin_pavel', NULL, NULL, 'admin')
ON CONFLICT (telegram_id) DO NOTHING;

-- Тестовые сделки
INSERT INTO deals (buyer_id, seller_id, amount, status, currency, payment_status, buyer_confirm, seller_confirm, creation_confirmed) VALUES
(1, 2, 1500.00, 'completed', 'BTC', 'confirmed', true, true, true),
(3, 2, 3000.00, 'awaiting_payment', 'TON', 'pending', true, true, true),
(1, 3, 500.00, 'awaiting_confirmation', 'BTC', 'pending', false, false, false);

-- Тестовые транзакции
INSERT INTO transactions (deal_id, amount, currency, garant_wallet, receiver_wallet, status) VALUES
(1, 1500.00, 'BTC', 'bc1qgarant123', 'bc1qtest456seller', 'completed'),
(2, 3000.00, 'TON', 'UQGarant456', 'UQTest456seller', 'pending');

-- Тестовые админы
INSERT INTO admins (name, login, password_hash, access_rights) VALUES
('Павел Админов', 'admin_pavel', '$2b$12$test_hash_admin', 'users:rw,deals:rw,admins:rw'),
('Катя Модератор', 'mod_kate', '$2b$12$test_hash_mod', 'users:r,deals:rw');

-- Тестовые логи событий
INSERT INTO event_log (initiator_id, action, details) VALUES
(1, 'deal_created', '{"deal_id": 1, "amount": 1500.00, "currency": "BTC"}'),
(2, 'deal_completed', '{"deal_id": 1, "status": "completed"}'),
(3, 'user_registered', '{"telegram_id": 555555555, "username": "trader_maria"}'),
(1, 'payment_received', '{"deal_id": 2, "amount": 3000.00}');
