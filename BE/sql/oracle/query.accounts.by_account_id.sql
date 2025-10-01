SELECT
  account_id,
  name,
  balance
FROM accounts
WHERE account_id = :account_id
ORDER BY account_id