-- PostgreSQL 데이터 초기화 및 IDENTITY 시퀀스 리셋 (TRUNCATE 버전 - 로그 없음, 빠름)
-- 주의: TRUNCATE는 롤백 불가능

-- 1. 트랜잭션 데이터 삭제 (TRUNCATE는 자동으로 IDENTITY 시퀀스 리셋)
-- RESTART IDENTITY 옵션으로 시퀀스 자동 리셋
-- CASCADE 옵션으로 FK 제약 무시
TRUNCATE TABLE ledger_entries, holds, transactions RESTART IDENTITY CASCADE;

-- 2. 계정 잔액 초기화
UPDATE accounts
SET balance = 0, hold_amount = 0;

-- 3. 특정 계정에 초기 잔액 설정 (테스트용)
UPDATE accounts
SET balance = 100000000
WHERE account_id IN (400001,400002,400003,400004,400005);

-- 확인 쿼리 (옵션)
-- SELECT 'transactions' as table_name, COUNT(*) as row_count FROM transactions
-- UNION ALL
-- SELECT 'holds', COUNT(*) FROM holds
-- UNION ALL
-- SELECT 'ledger_entries', COUNT(*) FROM ledger_entries
-- UNION ALL
-- SELECT 'accounts with balance', COUNT(*) FROM accounts WHERE balance > 0;
