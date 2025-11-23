-- Oracle 데이터 초기화 및 IDENTITY 시퀀스 리셋 (TRUNCATE 버전 - 락 없음, 빠름)
-- PostgreSQL, MySQL과 동일한 방식 적용

-- 1. 트랜잭션 데이터 삭제 (TRUNCATE는 락 없이 즉시 삭제, IDENTITY 시퀀스 자동 리셋)
-- 자식 테이블부터 TRUNCATE (FK 제약 때문)
TRUNCATE TABLE ledger_entries;
TRUNCATE TABLE holds;
TRUNCATE TABLE transactions;

-- 2. 계정 잔액 초기화
UPDATE accounts
SET balance = 0, hold_amount = 0;

-- 3. 특정 계정에 초기 잔액 설정 (테스트용)
UPDATE accounts
SET balance = 100000000
WHERE account_id IN (300001, 300002, 300003, 300004, 300005);

COMMIT;

-- 확인 쿼리 (옵션)
-- SELECT 'transactions' as table_name, COUNT(*) as row_count FROM transactions
-- UNION ALL
-- SELECT 'holds', COUNT(*) FROM holds
-- UNION ALL
-- SELECT 'ledger_entries', COUNT(*) FROM ledger_entries
-- UNION ALL
-- SELECT 'accounts with balance', COUNT(*) FROM accounts WHERE balance > 0;
