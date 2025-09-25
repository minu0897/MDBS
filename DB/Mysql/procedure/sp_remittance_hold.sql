-- ---------------------------------------
--               PROCEDURE              --
-- ---------------------------------------
-- DBMS :MySQL
-- Title : 송금(보류)
-- Detail : 송금(보류) 프로시저
CREATE PROCEDURE sp_remittance_hold(
    IN  p_src_account_id   BIGINT,
    IN  p_dst_account_id   BIGINT,
    IN  p_dst_bank         VARCHAR(2),
    IN  p_amount           DECIMAL(19,4),
    IN  p_idempotency_key  VARCHAR(100),
    IN  p_type             VARCHAR(1),
    OUT p_txn_id           BIGINT,
    OUT p_status           VARCHAR(1)
)
PROC:BEGIN
    DECLARE v_balance DECIMAL(19,4);
    DECLARE v_hold    DECIMAL(19,4);
    DECLARE v_txn_id  BIGINT;

    START TRANSACTION;

    -- 1) transactions 멱등 생성/재사용
    SET p_status = "1";
    INSERT INTO transactions(
        type,-- 1: 내부이체 2: 외부로 보냄 3: 외부에서 들어옴
        status,-- 1: 생성 완료 2: 원장 기장 완료 3: 정산 확정 4: 역분개 5: 잔액부족 6: 상대계좌x
        src_account_id,
        dst_account_id,
        dst_bank,
        amount,
        idempotency_key
    )
    VALUES (
        p_type,
        p_status,
        p_src_account_id,
        p_dst_account_id,
        p_dst_bank,
        p_amount,
        p_idempotency_key
    )
    ON DUPLICATE KEY UPDATE txn_id = LAST_INSERT_ID(txn_id);
    SET v_txn_id = LAST_INSERT_ID();

    -- 2) 출금 계좌 잠금 + 가용 금액 확인
    SELECT balance, hold_amount INTO v_balance, v_hold
      FROM accounts
     WHERE account_id = p_src_account_id
     FOR UPDATE;-- 조건에 맞는 ROW LOCK -> COMMIT; 시 UNLOCK

    -- 가용 금액 확인 후 없으면 status 5로 return
    IF v_balance - v_hold < p_amount THEN
        SET p_status = "5";
        UPDATE transactions SET status = p_status , updated_at=NOW() WHERE txn_id=v_txn_id; -- status='5' 실패
        COMMIT;
        LEAVE proc;  -- 끝
    END IF;

    -- 3) holds 멱등 생성
    INSERT INTO holds(
        account_id, 
        amount, 
        status, 
        idempotency_key
    )
    VALUES (
        p_src_account_id,
        p_amount,
        '1', -- OPEN (대기상태)
        p_idempotency_key
    )
    ON DUPLICATE KEY UPDATE hold_id = LAST_INSERT_ID(hold_id);

    -- 4) hold_amount 반영
    UPDATE accounts
       SET hold_amount = hold_amount + p_amount
     WHERE account_id   = p_src_account_id;


    COMMIT;

    SET p_txn_id = v_txn_id;
END
