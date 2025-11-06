-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 송금 보류 해제
-- Detail : 송금 보류(hold) 해제 프로시저 - 거래 실패 시 hold_amount 원상복구
CREATE OR REPLACE PROCEDURE MDBS.sp_remittance_release (
    p_idempotency_key IN  VARCHAR2,
    p_status          OUT VARCHAR2,    -- '3': RELEASED, '2': ALREADY_CAPTURED, '0': NOT_FOUND
    p_result          OUT VARCHAR2     -- 'OK' | 'ALREADY_RELEASED' | 'ALREADY_CAPTURED' | 'HOLD_NOT_FOUND'
) AS
    v_account NUMBER;
    v_amount  NUMBER;
    v_hstat   VARCHAR2(10);
    v_lock    NUMBER;  -- 더미 잠금용
BEGIN
    -- hold 조회
    BEGIN
        SELECT account_id, amount, status
          INTO v_account, v_amount, v_hstat
          FROM holds
         WHERE idempotency_key = p_idempotency_key
         FOR UPDATE;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_status := '0';
            p_result := 'HOLD_NOT_FOUND';
            RETURN;
    END;

    -- 이미 해제됨
    IF v_hstat = '3' THEN
        p_status := '3';
        p_result := 'ALREADY_RELEASED';
        RETURN;
    END IF;

    -- 이미 확정됨 (해제 불가)
    IF v_hstat = '2' THEN
        p_status := '2';
        p_result := 'ALREADY_CAPTURED';
        RETURN;
    END IF;

    -- 계좌 잠금
    SELECT 1 INTO v_lock FROM accounts WHERE account_id = v_account FOR UPDATE;

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

    p_status := '3';
    p_result := 'OK';
END;
/
