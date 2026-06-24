import sqlite3
from typing import List, Tuple

# ponytail: direct database connections without SQLAlchemy to save codebase size and dependencies

def get_sql_connection(db_type: str, params: dict, use_uri: bool) -> sqlite3.Connection:
    if db_type == "SQLite":
        return sqlite3.connect(params.get("sqlite_path", "sqlite.db"))
    
    uri = params.get("connection_uri", "") if use_uri else ""
    host = params.get("host", "localhost")
    port = params.get("port")
    user = params.get("username", "")
    password = params.get("password", "")
    database = params.get("database", "")
        
    if db_type == "PostgreSQL":
        import psycopg2
        if use_uri:
            return psycopg2.connect(uri)
        return psycopg2.connect(host=host, port=port or 5432, user=user, password=password, database=database)
        
    elif db_type == "MySQL":
        import pymysql
        if use_uri and uri.startswith("mysql://"):
            # Simple parse helper
            parts = uri[8:].split("@")
            creds, host_db = parts[0].split(":"), parts[1].split("/")
            user, password = creds[0], creds[1]
            host_port = host_db[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 3306
            database = host_db[1].split("?")[0]
        return pymysql.connect(host=host, port=int(port or 3306), user=user, password=password, database=database)
            
    raise ValueError(f"Unsupported DB: {db_type}")

def create_table_if_needed(conn, db_type: str, table_name: str, schema: dict, if_exists: str):
    cursor = conn.cursor()
    type_map = {
        "Integer": "INTEGER",
        "Float": "REAL",
        "Boolean": "BOOLEAN" if db_type != "SQLite" else "INTEGER",
        "Date": "DATE" if db_type != "SQLite" else "TEXT",
    }
    
    if if_exists == "replace":
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
    table_exists = False
    try:
        if db_type == "SQLite":
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = bool(cursor.fetchone())
        elif db_type == "PostgreSQL":
            cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
            table_exists = cursor.fetchone()[0]
        elif db_type == "MySQL":
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = bool(cursor.fetchone())
    except:
        pass
        
    if not table_exists or if_exists == "replace":
        cols_sql = []
        for col in schema.get("columns", []):
            col_name = col["name"]
            col_type = type_map.get(col["type"], "VARCHAR(255)")
            cols_sql.append(f"{col_name} {col_type}")
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(cols_sql)})")
        conn.commit()

def export_to_sql(db_type: str, params: dict, use_uri: bool, table_name: str, schema: dict, data: List[dict], if_exists: str) -> Tuple[bool, str]:
    try:
        conn = get_sql_connection(db_type, params, use_uri)
        create_table_if_needed(conn, db_type, table_name, schema, if_exists)
        
        cursor = conn.cursor()
        if not data:
            return True, "No rows to export."
            
        columns = [col["name"] for col in schema.get("columns", [])]
        placeholder = "?" if db_type == "SQLite" else "%s"
        placeholders = ", ".join([placeholder] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        for row in data:
            vals = [row.get(col) for col in columns]
            cursor.execute(insert_sql, vals)
            
        conn.commit()
        conn.close()
        return True, f"Successfully exported {len(data)} rows to {db_type} table '{table_name}'."
    except Exception as e:
        return False, str(e)

def export_to_mongo(params: dict, use_uri: bool, db_name: str, col_name: str, data: List[dict], if_exists: str) -> Tuple[bool, str]:
    try:
        import pymongo
        if use_uri:
            client = pymongo.MongoClient(params.get("connection_uri", ""))
        else:
            host = params.get("host", "localhost")
            port = int(params.get("port") or 27017)
            user = params.get("username", "")
            password = params.get("password", "")
            client = pymongo.MongoClient(host=host, port=port, username=user or None, password=password or None)
            
        db = client[db_name]
        collection = db[col_name]
        
        if if_exists == "replace":
            collection.delete_many({})
        elif if_exists == "fail" and collection.count_documents({}) > 0:
            return False, f"Collection '{col_name}' already exists and contains data."
            
        if data:
            collection.insert_many(data)
        return True, f"Successfully exported {len(data)} documents to MongoDB collection '{db_name}.{col_name}'."
    except Exception as e:
        return False, str(e)
