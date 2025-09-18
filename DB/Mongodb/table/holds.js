db.createCollection("holds", {
    validator: { $jsonSchema: {
      bsonType: "object",
      required: ["account_id","amount","status","idempotency_key","created_at"],
      properties: {
        account_id:      { bsonType: "objectId" },
        amount:          { bsonType: "decimal" },
        status:          { bsonType: "string", minLength: 1, maxLength: 1, },
        idempotency_key: { bsonType: "string", minLength: 1, maxLength: 100 },
        created_at:      { bsonType: "date" },
        updated_at:      { bsonType: ["date","null"] }
      }
    }}, validationLevel: "strict"
  });