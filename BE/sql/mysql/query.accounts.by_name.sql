SELECT
  account_id,
  name,
  balance
FROM MDBS.accounts
WHERE name LIKE CONCAT(%(name)s, '%%')
ORDER BY account_id;