-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS : PostgreSQL
-- Title : 송금(보류)
-- Detail : 송금(보류) 프로시저
CREATE OR REPLACE FUNCTION sp_remittance_hold(
    p_src_account_id   bigint,
    p_dst_account_id   bigint,
    p_dst_bank         text,
    p_amount           numeric,
    p_idempotency_key  text,
    p_type             text
) RETURNS TABLE (p_txn_id bigint, p_status text)
LANGUAGE plpgsql
AS $$
DECLARE
  v_balance NUMERIC(19,4);
  v_hold    NUMERIC(19,4);
BEGIN
  -- 1) 보류 생성 (멱등)
  p_status := '1';
  INSERT INTO transactions(type, status, src_account_id, dst_account_id, dst_bank, amount, idempotency_key)
  VALUES (p_type, p_status, p_src_account_id, p_dst_account_id, p_dst_bank, p_amount, p_idempotency_key)
  ON CONFLICT (idempotency_key)
  DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
  RETURNING txn_id INTO p_txn_id;

  -- 2) 계좌 존재 확인 및 가용금 확인
  SELECT balance, hold_amount
    INTO v_balance, v_hold
    FROM accounts
   WHERE account_id = p_src_account_id
   FOR UPDATE;

  -- 계좌가 존재하지 않으면 status 6으로 return
  IF v_balance IS NULL THEN
    p_status := '6'; -- 계좌없음
    UPDATE transactions SET status = p_status WHERE txn_id = p_txn_id;

    -- 결과 한 행을 실제로 내보내기
    RETURN QUERY SELECT p_txn_id, p_status;
    RETURN;
  END IF;

  IF v_balance - v_hold < p_amount THEN
    p_status := '5'; -- 잔액부족
    UPDATE transactions SET status = p_status WHERE txn_id = p_txn_id;

    -- 결과 한 행을 실제로 내보내기
    RETURN QUERY SELECT p_txn_id, p_status;
    RETURN;
  END IF;

  -- 3) holds 멱등 + hold 증가
  INSERT INTO holds(account_id, amount, status, idempotency_key)
  VALUES (p_src_account_id, p_amount, '1', p_idempotency_key)
  ON CONFLICT (idempotency_key) DO NOTHING;

  UPDATE accounts
     SET hold_amount = hold_amount + p_amount
   WHERE account_id = p_src_account_id;

  -- 정상 케이스도 한 행을 내보내기
  RETURN QUERY SELECT p_txn_id, p_status;
END;
$$;
