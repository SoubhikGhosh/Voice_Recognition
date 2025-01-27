import psycopg2

DB_CONFIG = {
    "dbname": "voice_db",
    "user": "soubhikghosh",
    "password": "99Ghosh@",  # Provide a password if set
    "host": "localhost",
    "port": 5432
}

def test_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connection successful!")
        conn.close()
        return "Connection successful!"
    except Exception as e:
        print("Connection failed:", e)
        return "Connection not successful!"