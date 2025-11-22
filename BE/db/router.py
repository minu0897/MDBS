# db/router.py
from flask import current_app
from .mysql_adapter import MySQLAdapter
from .postgres_adapter import PostgresAdapter
from .oracle_adapter import OracleAdapter
from .mongo_adapter import MongoAdapter

def get_adapter(dbms: str):
    """
    dbms: 'mysql' | 'postgres' | 'oracle' | 'mongo'
    """
    d = (dbms or "").lower()
    cfg = current_app.config

    if d == "mysql":
        return MySQLAdapter(cfg["MYSQL"])
    if d == "postgres":
        return PostgresAdapter(cfg["POSTGRES"])
    if d == "oracle":
        return OracleAdapter(cfg["ORACLE"])
    if d == "mongo":
        return MongoAdapter({
            "uri": cfg["MONGO_URI"],
            "db": cfg.get("MONGO_DB", "mdbs")
        })
    raise ValueError(f"Unsupported DBMS: {dbms}")
