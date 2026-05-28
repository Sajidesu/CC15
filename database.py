import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# Create the connection pool
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="attendance_pool",
        pool_size=10,
        pool_reset_session=True,
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "your_mysql_password"),
        database=os.getenv("DB_NAME", "attendance_system")
    )
    print("MySQL connection pool created.")
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")

# Dependency function to yield a database connection
def get_db():
    conn = db_pool.get_connection()
    try:
        yield conn  # Hands the connection to the FastAPI route
    finally:
        conn.close() # Automatically returns the connection to the pool when done