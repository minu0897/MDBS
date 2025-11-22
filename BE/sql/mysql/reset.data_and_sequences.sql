-- MySQL 데이터 초기화 및 Auto Increment 리셋 (DELETE 버전 - Foreign Key 안전)

-- 1. Foreign Key 체크 비활성화
SET FOREIGN_KEY_CHECKS = 0;

-- 2. 트랜잭션 데이터 삭제 (순서 중요: 자식 → 부모)
DELETE FROM MDBS.ledger_entries;
DELETE FROM MDBS.holds;
DELETE FROM MDBS.transactions;

-- 3. AUTO_INCREMENT 리셋
ALTER TABLE MDBS.ledger_entries AUTO_INCREMENT = 1;
ALTER TABLE MDBS.holds AUTO_INCREMENT = 1;
ALTER TABLE MDBS.transactions AUTO_INCREMENT = 1;

-- 4. Foreign Key 체크 재활성화
SET FOREIGN_KEY_CHECKS = 1;

-- 5. 계정 잔액 초기화
UPDATE MDBS.accounts
SET balance = 0, hold_amount = 0;

-- 6. 특정 계정에 초기 잔액 설정 (테스트용)
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
