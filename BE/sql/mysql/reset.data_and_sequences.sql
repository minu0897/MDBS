SET autocommit = 1;
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS MDBS.ledger_entries_temp;
CREATE TABLE MDBS.ledger_entries_temp LIKE MDBS.ledger_entries;
DROP TABLE MDBS.ledger_entries;
RENAME TABLE MDBS.ledger_entries_temp TO MDBS.ledger_entries;
DROP TABLE IF EXISTS MDBS.holds_temp;
CREATE TABLE MDBS.holds_temp LIKE MDBS.holds;
DROP TABLE MDBS.holds;
RENAME TABLE MDBS.holds_temp TO MDBS.holds;
DROP TABLE IF EXISTS MDBS.transactions_temp;
CREATE TABLE MDBS.transactions_temp LIKE MDBS.transactions;
DROP TABLE MDBS.transactions;
RENAME TABLE MDBS.transactions_temp TO MDBS.transactions;
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
