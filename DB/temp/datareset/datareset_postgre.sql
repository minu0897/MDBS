update accounts
set balance = 0, hold_amount = 0 

update accounts
set balance = 100000000
where account_id = 400001 or account_id = 400101

delete from holds

delete from ledger_entries

delete from  transactions