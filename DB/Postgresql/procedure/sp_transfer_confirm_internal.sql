-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 이체 확정
-- Detail : 이체 확정(입/출 같은은행) 프로시저
CREATE OR REPLACE FUNCTION sp_transfer_confirm_internal(
  p_idempotency_key TEXT
)
RETURNS TABLE (p_status TEXT, p_result TEXT)
LANGUAGE plpgsql AS
$$
DECLARE
  v_txn_id BIGINT;
  v_src    BIGINT;
  v_dst    BIGINT;
  v_amt    NUMERIC(19,4);
  v_hstat  TEXT;
  v_a      BIGINT;
  v_b      BIGINT;
BEGIN
  SELECT txn_id, src_account_id, dst_account_id, amount
    INTO v_txn_id, v_src, v_dst, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  SELECT status INTO v_hstat
    FROM holds
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  IF v_hstat = '2' THEN
    p_status := '2';
    p_result := 'ALREADY_CONFIRMED';
    RETURN;
  END IF;

  v_a := LEAST(v_src, v_dst);
  v_b := GREATEST(v_src, v_dst);

  -- 고정 순서 잠금
  PERFORM 1 FROM accounts WHERE account_id = v_a FOR UPDATE;
  PERFORM 1 FROM accounts WHERE account_id = v_b FOR UPDATE;

  -- 출금 확정
  UPDATE accounts
     SET hold_amount = hold_amount - v_amt,
         balance     = balance     - v_amt
   WHERE account_id = v_src;

  -- 입금 확정
  UPDATE accounts
     SET balance = balance + v_amt
   WHERE account_id = v_dst;

  -- 분개(2줄)
  INSERT INTO ledger_entries(txn_id, account_id, amount)
  VALUES (v_txn_id, v_src, -v_amt)
  ON CONFLICT DO NOTHING;

  INSERT INTO ledger_entries(txn_id, account_id, amount)
  VALUES (v_txn_id, v_dst,  v_amt)
  ON CONFLICT DO NOTHING;

  UPDATE holds        SET status='2' WHERE idempotency_key = p_idempotency_key;
  UPDATE transactions SET status='2' WHERE txn_id = v_txn_id;

  p_status := '2';
  p_result := 'OK';
  RETURN;
END;
$$;
