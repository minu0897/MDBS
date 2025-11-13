SELECT
  account_id,
  name,
  balance
FROM accounts
WHERE name LIKE :name || '%%'
ORDER BY account_id