-- ---------------------------------------
--              PROCEDURE              --
-- ---------------------------------------
-- Title : 출금 확정
-- Detail : 출금 확정 프로시저
CREATE PROCEDURE sp_confirm_debit_local(
    IN  p_idempotency_key VARCHAR(100),
    OUT p_txn_id          BIGINT,
    OUT p_status          VARCHAR(1),
    OUT p_result          VARCHAR(32)
)
proc:BEGIN
    DECLARE v_txn_id BIGINT;
    DECLARE v_src BIGINT;
    DECLARE v_amt DECIMAL(19,4);
    DECLARE v_hstat TINYINT;

    START TRANSACTION;

    -- 거래 조회(출금 계좌/금액 확보)
    SELECT txn_id, src_account_id, amount
      INTO v_txn_id, v_src, v_amt
      FROM transactions
     WHERE idempotency_key = p_idempotency_key
     FOR UPDATE;

    -- hold 확인
    SELECT status INTO v_hstat
      FROM holds
     WHERE idempotency_key = p_idempotency_key
     FOR UPDATE;

    IF v_hstat IS NULL THEN-- hold 없음
        ROLLBACK;
        SET p_txn_id = v_txn_id;
        SET p_status = 1;               -- 거래 상태는 POSTED 전이므로 PENDING 등 정책에 맞게
        SET p_result = 'HOLD_NOT_FOUND';
        LEAVE proc;

    ELSEIF v_hstat = 3 THEN-- RELEASED: 확정 전 취소됨 → 확정 불가
        ROLLBACK;
        SET p_txn_id = v_txn_id;
        SET p_status = 1;               -- 또는 CANCELED=7을 도입해 7 반환
        SET p_result = 'HOLD_RELEASED';
        LEAVE proc;

    ELSEIF v_hstat = 2 THEN-- CAPTURED: 이미 확정(멱등)
        COMMIT;                          -- 변경 없이 잠금만 해제
        SET p_txn_id = v_txn_id;
        SET p_status = 2;                -- POSTED로 간주(정책에 맞게 조정)
        SET p_result = 'ALREADY_CONFIRMED';
        LEAVE proc;

    ELSEIF v_hstat = 1 THEN
        -- OPEN: 정상 진행 (여기서는 빠져나가지 않고 아래 확정 로직으로 계속)
        -- no-op: 아래 단계에서 계좌 잠금 → hold↓, balance 이동 → ledger 기록 → 상태 전이

        -- 출금 계좌 잠금
        SELECT account_id FROM accounts WHERE account_id = v_src FOR UPDATE;

        -- 출금 확정
        UPDATE accounts
        SET hold_amount = hold_amount - v_amt,
            balance     = balance     - v_amt
        WHERE account_id = v_src;

        -- 분개(출금 −)
        INSERT INTO ledger_entries(txn_id, account_id, amount)
        VALUES (v_txn_id, v_src, -v_amt);

        -- 상태 전이
        UPDATE holds SET status = 2 WHERE idempotency_key = p_idempotency_key;  -- CAPTURED

        -- 출금만 끝나도 POSTED
        UPDATE transactions SET status = 2 WHERE txn_id = v_txn_id; -- 2=POSTED

        COMMIT;

        SET p_txn_id = v_txn_id;
        SET p_status = '2';
        SET p_result = 'OK';

    END IF;
END