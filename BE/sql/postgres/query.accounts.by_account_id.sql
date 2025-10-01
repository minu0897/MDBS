SELECT
  account_id,
  name,
  balance
FROM accounts
WHERE account_id = %(account_id)s
ORDER BY account_id