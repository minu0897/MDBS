-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 출금 확정
-- Detail : 출금 확정 프로시저
CREATE OR REPLACE FUNCTION sp_confirm_debit_local(
  p_idempotency_key TEXT
)
RETURNS TABLE (p_txn_id BIGINT, p_status TEXT, p_result TEXT)
LANGUAGE plpgsql AS
$$
DECLARE
  v_src  BIGINT;
  v_amt  NUMERIC(19,4);
  v_hstat TEXT;
BEGIN
  -- 거래 조회(출금 계좌/금액 확보)
  SELECT txn_id, src_account_id, amount
    INTO p_txn_id, v_src, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  -- hold 확인 (없으면 NULL)
  SELECT status INTO v_hstat
    FROM holds
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  IF v_hstat IS NULL THEN
    p_status := '1';
    p_result := 'HOLD_NOT_FOUND';
    RETURN;
  ELSIF v_hstat = '3' THEN
    p_status := '1';
    p_result := 'HOLD_RELEASED';
    RETURN;
  ELSIF v_hstat = '2' THEN
    p_status := '2';
    p_result := 'ALREADY_CONFIRMED';
    RETURN;
  ELSE
    -- OPEN: 정상 진행
    PERFORM 1 FROM accounts WHERE account_id = v_src FOR UPDATE;

    UPDATE accounts
       SET hold_amount = hold_amount - v_amt,
           balance     = balance     - v_amt
     WHERE account_id   = v_src;

    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (p_txn_id, v_src, -v_amt)
    ON CONFLICT DO NOTHING;

    UPDATE holds        SET status = '2' WHERE idempotency_key = p_idempotency_key; -- CAPTURED
    UPDATE transactions SET status = '2' WHERE txn_id = p_txn_id;                   -- POSTED

    p_status := '2';
    p_result := 'OK';

    RETURN QUERY SELECT p_status, p_txn_id, p_result;
  END IF;
END;
$$;
