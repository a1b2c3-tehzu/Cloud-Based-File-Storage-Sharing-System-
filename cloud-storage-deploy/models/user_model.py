from werkzeug.security import generate_password_hash, check_password_hash
from models.db import db
import datetime

class User:
    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password
        self.id = None
        self.created_at = None
    
    def create(self):
        hashed_password = generate_password_hash(self.password)
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        params = (self.name, self.email, hashed_password)
        
        cursor = db.execute_query(query, params)
        if cursor:
            self.id = cursor.lastrowid
            return True
        return False
    
    @staticmethod
    def get_by_email(email):
        query = "SELECT * FROM users WHERE email = %s"
        result = db.fetch_one(query, (email,))
        return result
    
    @staticmethod
    def get_by_id(user_id):
        query = "SELECT * FROM users WHERE id = %s"
        result = db.fetch_one(query, (user_id,))
        return result
    
    @staticmethod
    def verify_password(user, password):
        if user and 'password' in user:
            return check_password_hash(user['password'], password)
        return False
    
    @staticmethod
    def email_exists(email):
        query = "SELECT id FROM users WHERE email = %s"
        result = db.fetch_one(query, (email,))
        return result is not None
