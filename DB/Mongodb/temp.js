// temp.js
db.createCollection("temp");

db.createCollection("temp", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id"],
      properties: {
        id: {
          bsonType: "int",
          description: "must be an integer"
        }
      }
    }
  }
});
