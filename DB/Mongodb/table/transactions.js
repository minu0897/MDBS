db.createCollection("transactions", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["type","status","amount","idempotency_key","created_at"],
    properties: {
      type:            { bsonType: "string", minLength: 1, maxLength: 1 },
      status:          { bsonType: "string", minLength: 1, maxLength: 1 },   // 기본값은 애플리케이션에서 셋
      src_account_id:  { bsonType: ["string","null"], maxLength: 7 },
      dst_account_id:  { bsonType: ["string","null"], maxLength: 7 },
      src_bank:        { bsonType: ["string","null"], maxLength: 2 },
      dst_bank:        { bsonType: ["string","null"], maxLength: 2 },
      amount:          { bsonType: "decimal" },
      idempotency_key: { bsonType: "string", minLength: 1, maxLength: 100 },
      created_at:      { bsonType: "date" },
      updated_at:      { bsonType: ["date","null"] }
    }
  }}, validationLevel: "strict"
});
  
//create index
db.transactions.createIndex({ idempotency_key: 1 }, { unique: true });