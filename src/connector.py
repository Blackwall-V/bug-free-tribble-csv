import logging
import urllib.parse
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import create_engine, text

# Configure logging
logger = logging.getLogger(__name__)

def build_db_url(db_type: str, params: Dict[str, Any], use_uri: bool = False) -> str:
    """Build a database connection string based on type and parameters."""
    if use_uri:
        raw_uri = params.get("connection_uri", "").strip()
        if not raw_uri:
            raise ValueError("Connection URI cannot be empty.")
        
        # Adjust common prefixes to match SQLAlchemy drivers
        if db_type == "PostgreSQL" and raw_uri.startswith("postgres://"):
            return raw_uri.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_type == "PostgreSQL" and raw_uri.startswith("postgresql://"):
            return raw_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif db_type == "MySQL" and raw_uri.startswith("mysql://"):
            return raw_uri.replace("mysql://", "mysql+pymysql://", 1)
        elif db_type == "SQL Server" and raw_uri.startswith("mssql://"):
            return raw_uri.replace("mssql://", "mssql+pymssql://", 1)
        return raw_uri

    if db_type == "SQLite":
        db_path = params.get("sqlite_path", "sqlite.db").strip()
        if not db_path:
            db_path = "sqlite.db"
        return f"sqlite:///{db_path}"

    host = params.get("host", "localhost").strip()
    port = str(params.get("port", "")).strip()
    username = params.get("username", "").strip()
    password = params.get("password", "")
    database = params.get("database", "").strip()

    # URL encode password to handle special characters (@, :, /, etc.)
    encoded_password = urllib.parse.quote_plus(password)
    encoded_username = urllib.parse.quote_plus(username)

    if db_type == "PostgreSQL":
        port_suffix = f":{port}" if port else ":5432"
        return f"postgresql+psycopg2://{encoded_username}:{encoded_password}@{host}{port_suffix}/{database}"
    
    elif db_type == "MySQL":
        port_suffix = f":{port}" if port else ":3306"
        return f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}{port_suffix}/{database}"

    elif db_type == "SQL Server":
        port_suffix = f":{port}" if port else ":1433"
        return f"mssql+pymssql://{encoded_username}:{encoded_password}@{host}{port_suffix}/{database}"
        
    else:
        raise ValueError(f"Unsupported SQL database type: {db_type}")


def test_sql_connection(db_type: str, params: Dict[str, Any], use_uri: bool = False) -> Tuple[bool, str]:
    """Test connection to a SQL-based database."""
    try:
        url = build_db_url(db_type, params, use_uri)
        # Set a short timeout (e.g. 5 seconds) to avoid freezing the UI on bad hosts
        engine = create_engine(url, connect_args={"connect_timeout": 5} if db_type in ["PostgreSQL", "MySQL"] else {})
        
        with engine.connect() as connection:
            # Run simple query to verify active connection
            connection.execute(text("SELECT 1"))
        return True, "Connection successful!"
    except Exception as e:
        logger.error(f"SQL Connection test failed: {e}")
        return False, str(e)


def export_to_sql(
    df: pd.DataFrame,
    db_type: str,
    params: Dict[str, Any],
    table_name: str,
    if_exists: str = "append",
    use_uri: bool = False
) -> Tuple[bool, str]:
    """Upload DataFrame to a SQL database table."""
    try:
        url = build_db_url(db_type, params, use_uri)
        engine = create_engine(url)
        
        # Write to SQL
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False
        )
        return True, f"Successfully exported {len(df)} rows to table '{table_name}' ({if_exists})."
    except Exception as e:
        logger.error(f"SQL export failed: {e}")
        return False, str(e)


def get_mongo_client(params: Dict[str, Any], use_uri: bool = False):
    """Retrieve PyMongo MongoClient instance based on parameters."""
    import pymongo
    if use_uri:
        uri = params.get("connection_uri", "").strip()
        if not uri:
            raise ValueError("MongoDB URI cannot be empty.")
        # Ensure it has standard prefix if omitted
        if not uri.startswith("mongodb://") and not uri.startswith("mongodb+srv://"):
            uri = "mongodb://" + uri
        return pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    host = params.get("host", "localhost").strip()
    port = params.get("port", 27017)
    username = params.get("username", "").strip()
    password = params.get("password", "")
    auth_db = params.get("auth_db", "admin").strip()
    
    if username and password:
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/?authSource={auth_db}"
    else:
        uri = f"mongodb://{host}:{port}/"
        
    return pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)


def test_mongo_connection(params: Dict[str, Any], use_uri: bool = False) -> Tuple[bool, str]:
    """Test connection to a MongoDB database."""
    try:
        client = get_mongo_client(params, use_uri)
        # Trigger connection check
        client.admin.command('ping')
        return True, "Connection to MongoDB successful!"
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False, str(e)


def export_to_mongo(
    df: pd.DataFrame,
    params: Dict[str, Any],
    db_name: str,
    collection_name: str,
    if_exists: str = "append",
    use_uri: bool = False
) -> Tuple[bool, str]:
    """Upload DataFrame to a MongoDB collection."""
    try:
        client = get_mongo_client(params, use_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Convert DataFrame to records dict
        records = df.to_dict(orient="records")
        if not records:
            return True, "No rows to export."

        if if_exists == "fail":
            # If collection has documents, raise exception
            if collection.count_documents({}) > 0:
                raise ValueError(f"Collection '{collection_name}' is not empty (if_exists is set to 'fail').")
        elif if_exists == "replace":
            # Clear collection first
            collection.delete_many({})
            
        # Write
        result = collection.insert_many(records)
        return True, f"Successfully exported {len(result.inserted_ids)} documents to MongoDB collection '{db_name}.{collection_name}'."
    except Exception as e:
        logger.error(f"MongoDB export failed: {e}")
        return False, str(e)
