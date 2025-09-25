-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 출금 확정
-- Detail : 출금 확정 프로시저
CREATE OR REPLACE PROCEDURE sp_confirm_debit_local (
  p_idempotency_key IN  VARCHAR2,
  p_txn_id          OUT NUMBER,
  p_status          OUT VARCHAR2,   -- '1'|'2'
  p_result          OUT VARCHAR2    -- 'OK' | 'HOLD_NOT_FOUND' | 'HOLD_RELEASED' | 'ALREADY_CONFIRMED'
) AS
  v_src    NUMBER;
  v_amt    NUMBER;
  v_hstat  VARCHAR2(10);
  v_lock   NUMBER;  -- 더미 잠금용
BEGIN
  -- 거래/출금계좌/금액 조회 (잠금)
  SELECT txn_id, src_account_id, amount
    INTO p_txn_id, v_src, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  -- hold 상태 조회 (잠금)
  BEGIN
    SELECT status INTO v_hstat
      FROM holds
     WHERE idempotency_key = p_idempotency_key
     FOR UPDATE;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      p_status := '1';
      p_result := 'HOLD_NOT_FOUND';
      RETURN;
  END;

  IF v_hstat = '3' THEN -- RELEASED
    p_status := '1';
    p_result := 'HOLD_RELEASED';
    RETURN;
  ELSIF v_hstat = '2' THEN -- CAPTURED(이미 확정)
    p_status := '2';
    p_result := 'ALREADY_CONFIRMED';
    RETURN;
  END IF;

  -- 정상 진행: 출금계좌 잠금
  SELECT 1 INTO v_lock FROM accounts WHERE account_id = v_src FOR UPDATE;

  UPDATE accounts
     SET hold_amount = hold_amount - v_amt,
         balance     = balance     - v_amt
   WHERE account_id   = v_src;

  -- 분개(출금: 음수), 멱등 보조
  BEGIN
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (p_txn_id, v_src, -v_amt);
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN NULL;
  END;

  UPDATE holds        SET status = '2' WHERE idempotency_key = p_idempotency_key; -- CAPTURED
  UPDATE transactions SET status = '2' WHERE txn_id = p_txn_id;                   -- POSTED

  p_status := '2';
  p_result := 'OK';
END;
/
