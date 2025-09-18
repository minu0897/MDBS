db.createCollection("accounts", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["_id","name","status","balance","hold_amount","created_at"],
    properties: {
      _id:         { bsonType: "string", minLength: 3 }, // 계좌번호
      name:        { bsonType: "string", minLength: 1, maxLength: 20 },
      status:      { bsonType: "string", minLength: 1, maxLength: 1 }, // 한 글자 코드
      balance:     { bsonType: "decimal" },      // Decimal128
      hold_amount: { bsonType: "decimal" },      // Decimal128
      created_at:  { bsonType: "date" },
      updated_at:  { bsonType: ["date","null"] }
    }
  }}, validationLevel: "strict"
});