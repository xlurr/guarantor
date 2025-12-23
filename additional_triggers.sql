-- ========================================
-- 1. AUDIT триггер для users
-- ========================================
CREATE OR REPLACE FUNCTION audit_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO event_log (initiator_id, action, details)
        VALUES (NEW.user_id, 'user_registered', 
                json_build_object('telegram_id', NEW.telegram_id, 'username', NEW.username)::text);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO event_log (initiator_id, action, details)
        VALUES (NEW.user_id, 'user_updated',
                json_build_object('changed_fields', 
                    CASE 
                        WHEN OLD.wallet_ton != NEW.wallet_ton THEN 'wallet_ton'
                        WHEN OLD.wallet_btc != NEW.wallet_btc THEN 'wallet_btc'
                        ELSE 'other'
                    END)::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION audit_user_changes();


-- ========================================
-- 2. Триггер для валидации транзакций
-- ========================================
CREATE OR REPLACE FUNCTION validate_transaction()
RETURNS TRIGGER AS $$
BEGIN
    -- Проверка что deal существует и не завершен
    IF NOT EXISTS (
        SELECT 1 FROM deals 
        WHERE deal_id = NEW.deal_id 
        AND status NOT IN ('completed', 'cancelled')
    ) THEN
        RAISE EXCEPTION 'Cannot create transaction for completed or non-existent deal';
    END IF;
    
    -- Автологирование создания транзакции
    INSERT INTO event_log (initiator_id, action, details)
    VALUES (NULL, 'transaction_created',
            json_build_object('transaction_id', NEW.transaction_id, 
                            'deal_id', NEW.deal_id, 
                            'amount', NEW.amount,
                            'currency', NEW.currency)::text);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_transaction
BEFORE INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION validate_transaction();


-- ========================================
-- 3. Триггер для истечения срока сделки
-- ========================================
CREATE OR REPLACE FUNCTION check_deal_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expiry_time IS NOT NULL AND NEW.expiry_time < NOW() THEN
        NEW.status := 'expired';
        INSERT INTO event_log (initiator_id, action, details)
        VALUES (NULL, 'deal_expired',
                json_build_object('deal_id', NEW.deal_id, 'expiry_time', NEW.expiry_time)::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_expiry
BEFORE UPDATE ON deals
FOR EACH ROW
WHEN (NEW.expiry_time IS NOT NULL)
EXECUTE FUNCTION check_deal_expiry();


-- ========================================
-- 4. RULE: защита от случайного удаления завершенных сделок
-- ========================================
CREATE OR REPLACE RULE prevent_completed_deal_delete AS
ON DELETE TO deals
WHERE OLD.status = 'completed'
DO INSTEAD (
    INSERT INTO event_log (initiator_id, action, details)
    VALUES (NULL, 'delete_prevented',
            json_build_object('deal_id', OLD.deal_id, 'reason', 'completed_deal_protected')::text);
    SELECT NULL;  -- Отменяем удаление
);


-- ========================================
-- 5. CHECK constraint для admins
-- ========================================
ALTER TABLE admins 
ADD CONSTRAINT chk_admin_access_format 
CHECK (access_rights ~ '^([a-z_]+:[rw]+)(,[a-z_]+:[rw]+)*$');
