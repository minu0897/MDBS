-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 송금(보류)
-- Detail : 송금(보류) 프로시저
CREATE OR REPLACE PROCEDURE sp_remittance_hold (
  p_src_account_id   IN  NUMBER,
  p_dst_account_id   IN  NUMBER,
  p_dst_bank         IN  VARCHAR2,
  p_amount           IN  NUMBER,
  p_idempotency_key  IN  VARCHAR2,
  p_type             IN  VARCHAR2,
  p_txn_id           OUT NUMBER,
  p_status           OUT VARCHAR2      -- '1': 보류 생성, '5': 잔액부족
) AS
  v_balance   NUMBER;
  v_hold      NUMBER;
BEGIN
  p_status := '1';

  -- transactions 멱등 생성(INSERT 시도)
  BEGIN
    INSERT INTO transactions(type, status, src_account_id, dst_account_id, dst_bank, amount, idempotency_key)
    VALUES (p_type, p_status, p_src_account_id, p_dst_account_id, p_dst_bank, p_amount, p_idempotency_key)
    RETURNING txn_id INTO p_txn_id;
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
      SELECT txn_id INTO p_txn_id
        FROM transactions
       WHERE idempotency_key = p_idempotency_key
       FOR UPDATE;
  END;

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
  BEGIN
    INSERT INTO holds(account_id, amount, status, idempotency_key)
    VALUES (p_src_account_id, p_amount, '1', p_idempotency_key); -- '1': OPEN
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
      NULL; -- 이미 존재 → 통과
  END;

  -- hold 증가
  UPDATE accounts
     SET hold_amount = hold_amount + p_amount
   WHERE account_id = p_src_account_id;

END;
/
