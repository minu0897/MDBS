BEGIN
  -- 1. TRUNCATE로 빠르게 삭제 + IDENTITY 자동 리셋
  EXECUTE IMMEDIATE 'TRUNCATE TABLE ledger_entries';
  EXECUTE IMMEDIATE 'TRUNCATE TABLE holds';
  EXECUTE IMMEDIATE 'TRUNCATE TABLE transactions';

  -- 2. 계정 잔액 초기화
  UPDATE accounts SET balance = 0, hold_amount = 0;
  UPDATE accounts SET balance = 100000000 WHERE account_id IN (300001, 300002, 300003, 300004, 300005);

  COMMIT;
END;

-- 확인 쿼리 (옵션)
-- SELECT 'transactions' as table_name, COUNT(*) as row_count FROM transactions
-- UNION ALL
-- SELECT 'holds', COUNT(*) FROM holds
-- UNION ALL
-- SELECT 'ledger_entries', COUNT(*) FROM ledger_entries
-- UNION ALL
-- SELECT 'accounts with balance', COUNT(*) FROM accounts WHERE balance > 0;
