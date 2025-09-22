-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- Title : 입금 확정
-- Detail : 입금 확정 프로시저
CREATE PROCEDURE sp_confirm_credit_local(
    IN  p_idempotency_key VARCHAR(100),
    OUT p_txn_id          BIGINT,
    OUT p_status          VARCHAR(1),
    OUT p_result          VARCHAR(32)
)
proc:BEGIN
    DECLARE v_txn_id BIGINT;
    DECLARE v_dst BIGINT;
    DECLARE v_amt DECIMAL(19,4);

    START TRANSACTION;

    -- 거래 조회(입금 계좌/금액)
    SELECT txn_id, dst_account_id, amount
      INTO v_txn_id, v_dst, v_amt
      FROM transactions
     WHERE idempotency_key = p_idempotency_key
     FOR UPDATE;

    -- 멱등: 이미 해당 분개가 존재하면 이미 처리된 것으로 간주 (선택적으로 UNIQUE(txn_id,account_id,amount) 인덱스 권장)
    IF EXISTS (
        SELECT 1 FROM ledger_entries
         WHERE txn_id = v_txn_id AND account_id = v_dst AND amount = v_amt
    ) THEN
        COMMIT;
        SET p_txn_id = v_txn_id;
        SET p_status = '2';
        SET p_result = 'ALREADY_POSTED';
        LEAVE proc;
    END IF;

    -- 입금 계좌 잠금
    SELECT account_id FROM accounts WHERE account_id = v_dst FOR UPDATE;

    -- 입금 확정
    UPDATE accounts
       SET balance = balance + v_amt
     WHERE account_id = v_dst;

    -- 분개(입금 +)
    INSERT INTO ledger_entries(txn_id, account_id, amount)
    VALUES (v_txn_id, v_dst,  v_amt);

    -- 입금만 끝나도 POSTED
    UPDATE transactions SET status = 2 WHERE txn_id = v_txn_id;

    COMMIT;

    SET p_txn_id = v_txn_id;
    SET p_status = '2';
    SET p_result = 'OK';
END