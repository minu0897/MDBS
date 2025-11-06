UPDATE MDBS.accounts
set balance = 0, hold_amount = 0; 

update MDBS.accounts
set balance = 100000000
where account_id = 200001 or account_id = 200101;

delete from MDBS.holds;

delete from MDBS.ledger_entries;

delete from  MDBS.transactions;