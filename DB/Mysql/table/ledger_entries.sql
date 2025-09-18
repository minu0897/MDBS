CREATE TABLE ledger_entries (
  entry_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
  txn_id      BIGINT NOT NULL,
  account_id  BIGINT NOT NULL,
  amount      DECIMAL(19,4) NOT NULL, -- +입금, -출금
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_ledger_txn FOREIGN KEY (txn_id) REFERENCES transactions(txn_id),
  CONSTRAINT fk_ledger_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;