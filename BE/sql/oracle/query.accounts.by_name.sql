SELECT
  account_id,
  name,
  balance
FROM MDBS.accounts
WHERE name LIKE :name || '%%'
ORDER BY account_id