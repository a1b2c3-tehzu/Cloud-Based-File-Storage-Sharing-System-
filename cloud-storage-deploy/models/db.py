import mysql.connector
from mysql.connector import Error
import sqlite3
from config import Config

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        # Use MySQL directly
        try:
            self.connection = mysql.connector.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
                return True
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return False
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
    
    def execute_query(self, query, params=None):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except Error as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()
            return None
    
    def fetch_query(self, query, params=None):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching query: {e}")
            return None
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error fetching one: {e}")
            return None
        finally:
            cursor.close()

# Database instance
db = Database()
