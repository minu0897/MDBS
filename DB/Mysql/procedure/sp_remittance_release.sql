-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS :MySQL
-- Title : 송금 보류 해제
-- Detail : 송금 보류(hold) 해제 프로시저 - 거래 실패 시 hold_amount 원상복구
CREATE PROCEDURE sp_remittance_release(
    IN  p_idempotency_key VARCHAR(100),
    OUT p_status          VARCHAR(1),
    OUT p_result          VARCHAR(32)
)
PROC:BEGIN
    DECLARE v_account BIGINT;
    DECLARE v_amount DECIMAL(19,4);
    DECLARE v_hstat VARCHAR(1);

    START TRANSACTION;

    -- hold 조회
    BEGIN
        DECLARE CONTINUE HANDLER FOR NOT FOUND
        BEGIN
            SET p_status = '0';
            SET p_result = 'HOLD_NOT_FOUND';
        END;

        SELECT account_id, amount, status
          INTO v_account, v_amount, v_hstat
          FROM holds
         WHERE idempotency_key = p_idempotency_key
         FOR UPDATE;
    END;

    -- hold 없음
    IF p_status = '0' THEN
        ROLLBACK;
        LEAVE PROC;
    END IF;

    -- 이미 해제됨
    IF v_hstat = '3' THEN
        SET p_status = '3';
        SET p_result = 'ALREADY_RELEASED';
        COMMIT;
        LEAVE PROC;
    END IF;

    -- 이미 확정됨 (해제 불가)
    IF v_hstat = '2' THEN
        SET p_status = '2';
        SET p_result = 'ALREADY_CAPTURED';
        COMMIT;
        LEAVE PROC;
    END IF;

    -- 계좌 잠금
    SELECT account_id FROM accounts WHERE account_id = v_account FOR UPDATE;

    -- hold_amount 감소
    UPDATE accounts
       SET hold_amount = hold_amount - v_amount
     WHERE account_id = v_account;

    -- hold 상태 변경
    UPDATE holds
       SET status = '3'  -- RELEASED
     WHERE idempotency_key = p_idempotency_key;

    -- 거래 상태 업데이트 (선택적)
    UPDATE transactions
       SET status = '4'  -- REVERSED (역분개)
     WHERE idempotency_key = p_idempotency_key;

    COMMIT;

    SET p_status = '3';
    SET p_result = 'OK';
END
