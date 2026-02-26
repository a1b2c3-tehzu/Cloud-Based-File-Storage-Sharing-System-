from models.db import db
import datetime

class File:
    def __init__(self, user_id=None, file_name=None, file_size=0, folder_id=None, s3_key=None, s3_url=None, is_public=False):
        self.user_id = user_id
        self.file_name = file_name
        self.file_size = file_size
        self.folder_id = folder_id
        self.s3_key = s3_key
        self.s3_url = s3_url
        self.is_public = is_public
        self.id = None
        self.created_at = None
    
    def create(self):
        query = "INSERT INTO files (user_id, file_name, file_size, folder_id, s3_key, s3_url, is_public) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        params = (self.user_id, self.file_name, self.file_size, self.folder_id, self.s3_key, self.s3_url, self.is_public)
        
        cursor = db.execute_query(query, params)
        if cursor:
            self.id = cursor.lastrowid
            return True
        return False
    
    @staticmethod
    def get_by_user(user_id, folder_id=None):
        if folder_id is None:
            query = "SELECT * FROM files WHERE user_id = %s AND folder_id IS NULL ORDER BY created_at DESC"
            result = db.fetch_query(query, (user_id,))
        else:
            query = "SELECT * FROM files WHERE user_id = %s AND folder_id = %s ORDER BY created_at DESC"
            result = db.fetch_query(query, (user_id, folder_id))
        return result if result else []
    
    @staticmethod
    def get_by_id(file_id):
        query = "SELECT * FROM files WHERE id = %s"
        result = db.fetch_one(query, (file_id,))
        return result
    
    @staticmethod
    def delete(file_id, user_id):
        query = "DELETE FROM files WHERE id = %s AND user_id = %s"
        cursor = db.execute_query(query, (file_id, user_id))
        return cursor is not None
    
    @staticmethod
    def get_file_owner(file_id):
        query = "SELECT user_id FROM files WHERE id = %s"
        result = db.fetch_one(query, (file_id,))
        return result['user_id'] if result else None
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def create_multiple(files_data):
        """Create multiple file records in batch"""
        if not files_data:
            return []
        
        created_files = []
        for file_data in files_data:
            try:
                new_file = File(
                    user_id=file_data['user_id'],
                    file_name=file_data['file_name'],
                    file_size=file_data['file_size'],
                    folder_id=file_data.get('folder_id'),
                    s3_key=file_data['s3_key'],
                    s3_url=file_data['s3_url']
                )
                if new_file.create():
                    created_files.append(new_file)
            except Exception as e:
                print(f"Error creating file record: {e}")
        
        return created_files
    
    @staticmethod
    def move_to_folder(file_id, folder_id, user_id):
        """Move a file to a different folder"""
        query = "UPDATE files SET folder_id = %s WHERE id = %s AND user_id = %s"
        cursor = db.execute_query(query, (folder_id, file_id, user_id))
        return cursor is not None
    
    @staticmethod
    def file_exists(file_id):
        query = "SELECT id FROM files WHERE id = %s"
        result = db.fetch_one(query, (file_id,))
        return result is not None
