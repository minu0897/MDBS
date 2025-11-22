SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM MDBS.ledger_entries;
DELETE FROM MDBS.holds;
DELETE FROM MDBS.transactions;
ALTER TABLE MDBS.ledger_entries AUTO_INCREMENT = 1;
ALTER TABLE MDBS.holds AUTO_INCREMENT = 1;
ALTER TABLE MDBS.transactions AUTO_INCREMENT = 1;
SET FOREIGN_KEY_CHECKS = 1;
UPDATE MDBS.accounts SET balance = 0, hold_amount = 0;
UPDATE MDBS.accounts SET balance = 100000000 WHERE account_id IN (200001, 200002, 200003, 200004, 200005);

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
