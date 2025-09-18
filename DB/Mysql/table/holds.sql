CREATE TABLE `holds` (
  `hold_id` bigint NOT NULL AUTO_INCREMENT,
  `account_id` bigint NOT NULL,
  `amount` decimal(19,4) NOT NULL,
  `status` varchar(1) NOT NULL,
  `idempotency_key` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`hold_id`),
  UNIQUE KEY `ux_hold_idemp` (`idempotency_key`),
  KEY `fk_hold_account` (`account_id`),
  CONSTRAINT `fk_hold_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

