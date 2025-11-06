-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 입금 확정
-- Detail : 입금 확정 프로시저
CREATE OR REPLACE FUNCTION sp_confirm_credit_local(
  p_idempotency_key TEXT
)
RETURNS TABLE (p_txn_id BIGINT, p_status TEXT, p_result TEXT)
LANGUAGE plpgsql AS
$$
DECLARE
  v_dst BIGINT;
  v_amt NUMERIC(19,4);
  v_exists INT;
BEGIN
  SELECT txn_id, dst_account_id, amount
    INTO p_txn_id, v_dst, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  -- 멱등: 동일 분개가 이미 있으면 종료
  SELECT COUNT(*) INTO v_exists
    FROM ledger_entries
   WHERE txn_id = p_txn_id AND account_id = v_dst AND amount = v_amt;

  IF v_exists > 0 THEN
    p_status := '2';
    p_result := 'ALREADY_POSTED';
    RETURN;
  END IF;

  PERFORM 1 FROM accounts WHERE account_id = v_dst FOR UPDATE;

  UPDATE accounts
     SET balance = balance + v_amt
   WHERE account_id = v_dst;

  INSERT INTO ledger_entries(txn_id, account_id, amount)
  VALUES (p_txn_id, v_dst, v_amt)
  ON CONFLICT DO NOTHING;

  UPDATE transactions SET status = '2' WHERE txn_id = p_txn_id;

  p_status := '2';
  p_result := 'OK';

  RETURN QUERY SELECT p_txn_id, p_status, p_result;
END;
$$;
