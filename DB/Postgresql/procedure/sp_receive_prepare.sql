-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 수금(보류)
-- Detail : 수금(보류) 프로시저
CREATE OR REPLACE FUNCTION sp_receive_prepare(
  p_src_account_id  BIGINT,
  p_dst_account_id  BIGINT,
  p_dst_bank        TEXT,
  p_amount          NUMERIC(19,4),
  p_idempotency_key TEXT,
  p_type            TEXT
)
RETURNS TABLE (p_txn_id BIGINT, p_status TEXT)
LANGUAGE plpgsql AS
$$
DECLARE
  v_exists INT;
BEGIN
  p_status := '1';
  INSERT INTO transactions(
    type, status, src_account_id, dst_account_id, dst_bank, amount, idempotency_key
  ) VALUES (
    p_type, p_status, p_src_account_id, p_dst_account_id, p_dst_bank, p_amount, p_idempotency_key
  )
  ON CONFLICT (idempotency_key)
  DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
  RETURNING txn_id INTO p_txn_id;

  SELECT COUNT(*) INTO v_exists
    FROM accounts
   WHERE account_id = p_dst_account_id;

  IF v_exists = 0 THEN
    p_status := '6'; -- 상대 계좌 없음
    UPDATE transactions SET status = p_status WHERE txn_id = p_txn_id;
  END IF;

  RETURN QUERY SELECT p_status, p_txn_id;
END;
$$;
