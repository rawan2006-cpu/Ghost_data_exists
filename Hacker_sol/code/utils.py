import psycopg2
from psycopg2 import OperationalError

def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres123",
            host="localhost",
            port="5432"
        )
        return connection
    except OperationalError as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        return None

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("SUCCESS: Connected to PostgreSQL database successfully!")
        conn.close()