update accounts
set balance = 0, hold_amount = 0 

update accounts
set balance = 100000000
where account_id = 300001 or account_id = 300101

delete from holds

delete from ledger_entries

delete from  transactions