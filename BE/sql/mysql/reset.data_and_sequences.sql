-- MySQL 데이터 초기화 및 Auto Increment 리셋 (TRUNCATE 버전 - 로그 없음, 빠름)
-- 주의: TRUNCATE는 롤백 불가능, DDL 문이므로 암묵적 COMMIT 발생

-- 1. Foreign Key 체크 비활성화
SET FOREIGN_KEY_CHECKS = 0;

-- 2. 트랜잭션 데이터 삭제 (TRUNCATE는 자동으로 AUTO_INCREMENT 리셋)
TRUNCATE TABLE MDBS.ledger_entries;
TRUNCATE TABLE MDBS.holds;
TRUNCATE TABLE MDBS.transactions;

-- 3. Foreign Key 체크 재활성화
SET FOREIGN_KEY_CHECKS = 1;

-- 4. 계정 잔액 초기화
UPDATE MDBS.accounts
SET balance = 0, hold_amount = 0;

-- 5. 특정 계정에 초기 잔액 설정 (테스트용)
UPDATE MDBS.accounts
SET balance = 100000000
WHERE account_id IN (200001, 200002, 200003, 200004, 200005);

-- 확인 쿼리 (옵션)
-- SELECT 'transactions' as table_name, COUNT(*) as row_count, AUTO_INCREMENT as next_id
-- FROM information_schema.tables
-- WHERE table_schema = 'MDBS' AND table_name = 'transactions'
-- UNION ALL
-- SELECT 'holds', COUNT(*), AUTO_INCREMENT
-- FROM information_schema.tables
-- WHERE table_schema = 'MDBS' AND table_name = 'holds'
-- UNION ALL
-- SELECT 'ledger_entries', COUNT(*), AUTO_INCREMENT
-- FROM information_schema.tables
-- WHERE table_schema = 'MDBS' AND table_name = 'ledger_entries';
