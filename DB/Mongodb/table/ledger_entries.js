db.createCollection("ledger_entries", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["txn_id","account_id","amount","created_at"],
    properties: {
      txn_id:     { bsonType: "objectId" },
      account_id: { bsonType: "string", maxLength: 7 },
      amount:     { bsonType: "decimal" },
      created_at: { bsonType: "date" },
      updated_at: { bsonType: ["date","null"] }
    }
  }}, validationLevel: "strict"
});