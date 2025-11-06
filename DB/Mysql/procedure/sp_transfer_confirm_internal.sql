-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- DBMS :MySQL
-- Title : 이체 확정
-- Detail : 이체 확정(입/출 같은은행) 프로시저
CREATE PROCEDURE sp_transfer_confirm_internal(
    IN  p_idempotency_key VARCHAR(100),
    OUT p_status          VARCHAR(1),
    OUT p_result          VARCHAR(32)
)
PROC:BEGIN
    DECLARE v_txn_id BIGINT;
    DECLARE v_src BIGINT;
    DECLARE v_dst BIGINT;
    DECLARE v_amt DECIMAL(19,4);
    DECLARE v_hstat VARCHAR(1);
    DECLARE v_a BIGINT;
    DECLARE v_b BIGINT;

    START TRANSACTION;

    -- 0) txn 조회
    SELECT txn_id, src_account_id, dst_account_id, amount
      INTO v_txn_id, v_src, v_dst, v_amt
    FROM transactions
    WHERE idempotency_key = p_idempotency_key
    FOR UPDATE;

    -- 1) holds 상태 확인 (멱등 제어)
    SELECT status INTO v_hstat
    FROM holds
    WHERE idempotency_key = p_idempotency_key
    FOR UPDATE;

    IF v_hstat = '2' THEN -- 2: 확정
        -- 이미 확정 완료
        COMMIT;
        LEAVE proc;
        SET p_status = '2';
        SET p_result = 'ALREADY_CONFIRMED';
    END IF;

    -- 2) 잠금 순서 고정(교착 회피)
    SET v_a = LEAST(v_src, v_dst);-- LEAST로 더 작은 값
    SET v_b = GREATEST(v_src, v_dst);-- GREATEST로 더 큰 값

    -- FOR UPDATE로 해당 ROW LOCK
    SELECT account_id FROM accounts WHERE account_id IN (v_a, v_b) FOR UPDATE;

    -- 3) 출금 확정: hold_amount↓, balance↓
    UPDATE accounts
       SET hold_amount = hold_amount - v_amt,
           balance     = balance     - v_amt
     WHERE account_id = v_src;

    -- 4) 입금 확정: balance↑
    UPDATE accounts
       SET balance = balance + v_amt
     WHERE account_id = v_dst;

    -- 5) 분개(불변 로그) 2줄
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (v_txn_id, v_src, -v_amt);
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (v_txn_id, v_dst,  v_amt);

    -- 6) 상태 전이
    UPDATE holds        SET status='2' WHERE idempotency_key = p_idempotency_key;
    UPDATE transactions SET status='2' WHERE txn_id = v_txn_id;

    SET p_status = '2';
    SET p_result = 'OK';
    COMMIT;
END