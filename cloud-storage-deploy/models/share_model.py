from models.db import db
import datetime
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

class ShareLink:
    def __init__(self, file_id=None, token=None, expiry_date=None, password=None, max_downloads=None):
        self.file_id = file_id
        self.token = token
        self.expiry_date = expiry_date
        self.password = password
        self.max_downloads = max_downloads
        self.id = None
        self.created_at = None
        self.download_count = 0
        self.is_active = True
    
    @staticmethod
    def generate_token():
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(32))
    
    def create(self, expiry_hours=24):
        self.token = self.generate_token()
        expiry_time = datetime.datetime.now() + datetime.timedelta(hours=expiry_hours)
        self.expiry_date = expiry_time
        
        # Hash password if provided
        password_hash = None
        if self.password:
            password_hash = generate_password_hash(self.password)
        
        query = """
        INSERT INTO shared_links 
        (file_id, token, expiry_date, password_hash, max_downloads, download_count, is_active) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (self.file_id, self.token, self.expiry_date, password_hash, 
                 self.max_downloads, self.download_count, self.is_active)
        
        cursor = db.execute_query(query, params)
        if cursor:
            self.id = cursor.lastrowid
            return True
        return False
    
    @staticmethod
    def get_by_token(token):
        query = """
        SELECT sl.*, f.file_name, f.s3_url 
        FROM shared_links sl 
        JOIN files f ON sl.file_id = f.id 
        WHERE sl.token = %s AND sl.is_active = TRUE
        """
        result = db.fetch_one(query, (token,))
        return result
    
    @staticmethod
    def verify_password(share_link, password):
        if not share_link.get('password_hash'):
            return True  # No password required
        return check_password_hash(share_link['password_hash'], password)
    
    @staticmethod
    def increment_download_count(token):
        query = """
        UPDATE shared_links 
        SET download_count = download_count + 1 
        WHERE token = %s
        """
        cursor = db.execute_query(query, (token,))
        return cursor is not None
    
    @staticmethod
    def check_download_limit(token):
        query = """
        SELECT max_downloads, download_count 
        FROM shared_links 
        WHERE token = %s
        """
        result = db.fetch_one(query, (token,))
        if result:
            if result['max_downloads'] is None:
                return True  # No limit
            return result['download_count'] < result['max_downloads']
        return False
    
    @staticmethod
    def deactivate_link(token):
        query = "UPDATE shared_links SET is_active = FALSE WHERE token = %s"
        cursor = db.execute_query(query, (token,))
        return cursor is not None
    
    @staticmethod
    def is_valid(token):
        query = "SELECT * FROM shared_links WHERE token = %s AND expiry_date > NOW()"
        result = db.fetch_one(query, (token,))
        return result is not None
    
    @staticmethod
    def get_file_info(token):
        query = """
        SELECT f.*, sl.expiry_date 
        FROM files f 
        JOIN shared_links sl ON f.id = sl.file_id 
        WHERE sl.token = %s AND sl.expiry_date > NOW()
        """
        result = db.fetch_one(query, (token,))
        return result
    
    @staticmethod
    def delete_expired():
        query = "DELETE FROM shared_links WHERE expiry_date <= NOW()"
        cursor = db.execute_query(query)
        return cursor is not None
