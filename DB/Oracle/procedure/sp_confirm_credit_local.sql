-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 입금 확정
-- Detail : 입금 확정 프로시저
CREATE OR REPLACE PROCEDURE sp_confirm_credit_local (
  p_idempotency_key IN  VARCHAR2,
  p_txn_id          OUT NUMBER,
  p_status          OUT VARCHAR2,     -- '2'
  p_result          OUT VARCHAR2      -- 'OK' | 'ALREADY_POSTED'
) AS
  v_dst    NUMBER;
  v_amt    NUMBER;
  v_cnt    NUMBER;
  v_lock   NUMBER;  -- 더미 잠금용
BEGIN
  SELECT txn_id, dst_account_id, amount
    INTO p_txn_id, v_dst, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  -- 멱등: 동일 분개 존재?
  SELECT COUNT(*) INTO v_cnt
    FROM ledger_entries
   WHERE txn_id = p_txn_id AND account_id = v_dst AND amount = v_amt;

  IF v_cnt > 0 THEN
    p_status := '2';
    p_result := 'ALREADY_POSTED';
    RETURN;
  END IF;

  SELECT 1 INTO v_lock FROM accounts WHERE account_id = v_dst FOR UPDATE;

  UPDATE accounts
     SET balance = balance + v_amt
   WHERE account_id = v_dst;

  BEGIN
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (p_txn_id, v_dst, v_amt);
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN NULL;
  END;

  UPDATE transactions SET status = '2' WHERE txn_id = p_txn_id;

  p_status := '2';
  p_result := 'OK';
END;
/
