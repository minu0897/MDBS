CREATE TABLE `transactions` (
  `txn_id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(1) NOT NULL,
  `status` varchar(1) NOT NULL,
  `src_account_id` bigint DEFAULT NULL,
  `dst_account_id` bigint DEFAULT NULL,
  `src_bank` varchar(2) DEFAULT NULL,
  `dst_bank` varchar(2) DEFAULT NULL,
  `amount` decimal(19,4) NOT NULL,
  `idempotency_key` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`txn_id`),
  UNIQUE KEY `ux_txn_idemp` (`idempotency_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

