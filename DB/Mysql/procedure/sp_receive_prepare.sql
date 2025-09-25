-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS :MySQL
-- Title : 수금(보류)
-- Detail : 수금(보류) 프로시저
CREATE PROCEDURE sp_receive_prepare(
    IN  p_src_account_id BIGINT,
    IN  p_dst_account_id BIGINT,
    IN  p_dst_bank       VARCHAR(2),
    IN  p_amount         DECIMAL(19,4),
    IN  p_idempotency_key VARCHAR(100),
    IN  p_type             VARCHAR(1),
    OUT p_txn_id         BIGINT,
    OUT p_status           VARCHAR(1)
)
PROC:BEGIN
    DECLARE v_txn_id BIGINT;
    DECLARE v_exists INT;

    START TRANSACTION;
    SET p_status = '1';

    INSERT INTO transactions(
        type,
        status,
        src_account_id,
        dst_account_id,
        dst_bank,
        amount,
        idempotency_key)
    VALUES (
        p_type,
        p_status,
        p_src_account_id,
        p_dst_account_id,
        p_dst_bank,
        p_amount,
        p_idempotency_key)
    ON DUPLICATE KEY UPDATE txn_id = LAST_INSERT_ID(txn_id);

    SET v_txn_id = LAST_INSERT_ID();


    -- 수취 계좌 조회 없을시 status = 6으로 update
    SELECT COUNT(*) INTO v_exists
      FROM accounts
     WHERE account_id = p_dst_account_id;

    IF v_exists = 0 THEN
        -- 실패 기록 남기고 커밋, 에러는 던지지 않음
        SET p_status = '6';
        UPDATE transactions
           SET status = p_status
         WHERE txn_id = v_txn_id;

        COMMIT;

        SET p_txn_id = v_txn_id;

        LEAVE proc;  -- 끝
    END IF;

    COMMIT;

    SET p_txn_id = v_txn_id;
END