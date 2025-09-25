-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 이체 확정
-- Detail : 이체 확정(입/출 같은은행) 프로시저
CREATE OR REPLACE PROCEDURE sp_transfer_confirm_internal (
  p_idempotency_key IN  VARCHAR2,
  p_status          OUT VARCHAR2,    -- '2'
  p_result          OUT VARCHAR2     -- 'OK' | 'ALREADY_CONFIRMED'
) AS
  v_txn_id NUMBER;
  v_src    NUMBER;
  v_dst    NUMBER;
  v_amt    NUMBER;
  v_hstat  VARCHAR2(10);
  v_a      NUMBER;
  v_b      NUMBER;
  v_lock1   NUMBER;  -- 더미 잠금용
  v_lock2   NUMBER;  -- 더미 잠금용
BEGIN
  SELECT txn_id, src_account_id, dst_account_id, amount
    INTO v_txn_id, v_src, v_dst, v_amt
    FROM transactions
   WHERE idempotency_key = p_idempotency_key
   FOR UPDATE;

  BEGIN
    SELECT status INTO v_hstat
      FROM holds
     WHERE idempotency_key = p_idempotency_key
     FOR UPDATE;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      -- 비정상 케이스: hold 없음 → 출금 없이 입금만 일으키지 않도록 실패 처리하고 싶다면 여기서 반환/에러
      v_hstat := NULL;
  END;

  IF v_hstat = '2' THEN
    p_status := '2';
    p_result := 'ALREADY_CONFIRMED';
    RETURN;
  END IF;

  v_a := LEAST(v_src, v_dst);
  v_b := GREATEST(v_src, v_dst);

  -- 고정 순서로 계좌 잠금
  SELECT 1 INTO v_lock1 FROM accounts WHERE account_id = v_a FOR UPDATE;
  SELECT 1 INTO v_lock2 FROM accounts WHERE account_id = v_b FOR UPDATE;

  -- 출금 확정
  IF v_hstat IS NOT NULL THEN
    UPDATE accounts
       SET hold_amount = hold_amount - v_amt,
           balance     = balance     - v_amt
     WHERE account_id   = v_src;
  ELSE
    -- hold가 없을 경우, 정책상 단순 출금만 생략하고 입금 진행할지/실패시킬지는 업무정책에 맞추세요.
    -- 여기서는 hold 없을 때 출금을 생략하지 않고 에러로 보고 싶다면 RAISE_APPLICATION_ERROR 사용.
    NULL;
  END IF;

  -- 입금 확정
  UPDATE accounts
     SET balance = balance + v_amt
   WHERE account_id = v_dst;

  -- 분개(2줄), 멱등 보조
  BEGIN
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (v_txn_id, v_src, -v_amt);
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN NULL;
  END;

  BEGIN
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (v_txn_id, v_dst,  v_amt);
  EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN NULL;
  END;

  IF v_hstat IS NOT NULL THEN
    UPDATE holds SET status='2' WHERE idempotency_key = p_idempotency_key; -- CAPTURED
  END IF;

  UPDATE transactions SET status='2' WHERE txn_id = v_txn_id;              -- POSTED

  p_status := '2';
  p_result := 'OK';
END;
/
