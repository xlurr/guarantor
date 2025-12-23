-- Функция для обновления статистики пользователя при завершении сделки
CREATE OR REPLACE FUNCTION update_user_stats() 
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем статистику покупателя
    UPDATE users 
    SET total_deals = total_deals + 1,
        success_rate = (
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / NULLIF(COUNT(*), 0), 2
            )
            FROM deals 
            WHERE buyer_id = NEW.buyer_id OR seller_id = NEW.buyer_id
        )
    WHERE user_id = NEW.buyer_id;
    
    -- Обновляем статистику продавца
    UPDATE users 
    SET total_deals = total_deals + 1,
        success_rate = (
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / NULLIF(COUNT(*), 0), 2
            )
            FROM deals 
            WHERE buyer_id = NEW.seller_id OR seller_id = NEW.seller_id
        )
    WHERE user_id = NEW.seller_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер: вызывается при завершении сделки
CREATE TRIGGER trg_update_user_stats
AFTER UPDATE OF status ON deals
FOR EACH ROW
WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
EXECUTE FUNCTION update_user_stats();


-- Функция для автоматического логирования изменений статуса сделки
CREATE OR REPLACE FUNCTION log_deal_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status != OLD.status THEN
        INSERT INTO event_log (initiator_id, action, details)
        VALUES (
            NULL,
            'deal_status_changed',
            json_build_object(
                'deal_id', NEW.deal_id,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'buyer_id', NEW.buyer_id,
                'seller_id', NEW.seller_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер: логирование изменений статуса
CREATE TRIGGER trg_log_deal_status
AFTER UPDATE OF status ON deals
FOR EACH ROW
EXECUTE FUNCTION log_deal_status_change();


-- Функция: автоматическое вычисление комиссии (1% от суммы)
CREATE OR REPLACE FUNCTION calculate_commission()
RETURNS TRIGGER AS $$
BEGIN
    NEW.commission := NEW.amount * 0.01;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер: автоматический расчёт комиссии при создании сделки
CREATE TRIGGER trg_calculate_commission
BEFORE INSERT ON deals
FOR EACH ROW
EXECUTE FUNCTION calculate_commission();


-- Функция: валидация суммы сделки (не меньше 1)
CREATE OR REPLACE FUNCTION validate_deal_amount()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount < 1 THEN
        RAISE EXCEPTION 'Amount must be greater than or equal to 1';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер: валидация суммы
CREATE TRIGGER trg_validate_amount
BEFORE INSERT OR UPDATE OF amount ON deals
FOR EACH ROW
EXECUTE FUNCTION validate_deal_amount();
