-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 송금(보류)
-- Detail : 송금(보류) 프로시저
CREATE OR REPLACE FUNCTION sp_remittance_hold(
  p_src_account_id   BIGINT,
  p_dst_account_id   BIGINT,
  p_dst_bank         TEXT,
  p_amount           NUMERIC(19,4),
  p_idempotency_key  TEXT,
  p_type             TEXT
)
RETURNS TABLE (p_txn_id BIGINT, p_status TEXT)
LANGUAGE plpgsql AS
$$
DECLARE
  v_balance NUMERIC(19,4);
  v_hold    NUMERIC(19,4);
BEGIN
  -- transactions 멱등 생성/재사용
  p_status := '1'; -- 생성/보류
  INSERT INTO transactions(
      type, status, src_account_id, dst_account_id, dst_bank, amount, idempotency_key
  ) VALUES (
      p_type, p_status, p_src_account_id, p_dst_account_id, p_dst_bank, p_amount, p_idempotency_key
  )
  ON CONFLICT (idempotency_key)
  DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
  RETURNING txn_id INTO p_txn_id;

  -- 출금 계좌 잠금 + 가용금 확인
  SELECT balance, hold_amount
    INTO v_balance, v_hold
    FROM accounts
   WHERE account_id = p_src_account_id
   FOR UPDATE;

  IF v_balance - v_hold < p_amount THEN
    p_status := '5'; -- 잔액부족
    UPDATE transactions SET status = p_status WHERE txn_id = p_txn_id;
    RETURN;
  END IF;

  -- holds 멱등 생성
  INSERT INTO holds(account_id, amount, status, idempotency_key)
  VALUES (p_src_account_id, p_amount, '1', p_idempotency_key)  -- OPEN
  ON CONFLICT (idempotency_key)
  DO NOTHING;

  -- hold 증가
  UPDATE accounts
     SET hold_amount = hold_amount + p_amount
   WHERE account_id = p_src_account_id;

  RETURN; -- p_txn_id, p_status('1')
END;
$$;
