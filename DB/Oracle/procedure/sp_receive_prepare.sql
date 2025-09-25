-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS :Oracle
-- Title : 수금(보류)
-- Detail : 수금(보류) 프로시저
CREATE OR REPLACE PROCEDURE sp_receive_prepare (
  p_src_account_id   IN  NUMBER,
  p_dst_account_id   IN  NUMBER,
  p_dst_bank         IN  VARCHAR2,
  p_amount           IN  NUMBER,
  p_idempotency_key  IN  VARCHAR2,
  p_type             IN  VARCHAR2,
  p_txn_id           OUT NUMBER,
  p_status           OUT VARCHAR2      -- '1': 생성, '6': 수취계좌없음
) AS
  v_exists NUMBER;
BEGIN
  p_status := '1';

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

  SELECT COUNT(*) INTO v_exists
    FROM accounts
   WHERE account_id = p_dst_account_id;

  IF v_exists = 0 THEN
    p_status := '6'; -- 수취 계좌 없음
    UPDATE transactions SET status = p_status WHERE txn_id = p_txn_id;
  END IF;
END;
/
