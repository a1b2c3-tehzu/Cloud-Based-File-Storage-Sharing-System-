from models.db import db
import datetime

class ShareAnalytics:
    def __init__(self, share_link_id=None, ip_address=None, user_agent=None):
        self.share_link_id = share_link_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.id = None
        self.access_time = None
    
    @staticmethod
    def record_access(share_link_id, ip_address, user_agent):
        query = "INSERT INTO share_analytics (share_link_id, ip_address, user_agent) VALUES (%s, %s, %s)"
        params = (share_link_id, ip_address, user_agent)
        cursor = db.execute_query(query, params)
        return cursor is not None
    
    @staticmethod
    def get_share_stats(share_link_id):
        query = """
        SELECT COUNT(*) as total_accesses, 
               COUNT(DISTINCT ip_address) as unique_visitors,
               MIN(access_time) as first_access,
               MAX(access_time) as last_access
        FROM share_analytics 
        WHERE share_link_id = %s
        """
        result = db.fetch_one(query, (share_link_id,))
        return result
    
    @staticmethod
    def get_access_timeline(share_link_id, days=7):
        query = """
        SELECT DATE(access_time) as date, COUNT(*) as accesses
        FROM share_analytics 
        WHERE share_link_id = %s 
        AND access_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(access_time)
        ORDER BY date
        """
        return db.fetch_query(query, (share_link_id, days))

class UserAnalytics:
    def __init__(self, user_id=None, action_type=None, details=None):
        self.user_id = user_id
        self.action_type = action_type
        self.details = details
        self.id = None
        self.timestamp = None
    
    @staticmethod
    def record_action(user_id, action_type, details=None):
        query = "INSERT INTO user_analytics (user_id, action_type, details) VALUES (%s, %s, %s)"
        params = (user_id, action_type, details)
        cursor = db.execute_query(query, params)
        return cursor is not None
    
    @staticmethod
    def get_user_activity(user_id, days=30):
        query = """
        SELECT action_type, COUNT(*) as count, DATE(timestamp) as date
        FROM user_analytics 
        WHERE user_id = %s 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY action_type, DATE(timestamp)
        ORDER BY date DESC, count DESC
        """
        try:
            result = db.fetch_query(query, (user_id, days))
            return result if result else []
        except Exception as e:
            print(f"Error in get_user_activity: {e}")
            return []
    
    @staticmethod
    def get_login_frequency(user_id, days=30):
        query = """
        SELECT DATE(timestamp) as date, COUNT(*) as logins
        FROM user_analytics 
        WHERE user_id = %s 
        AND action_type = 'login'
        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
        try:
            result = db.fetch_query(query, (user_id, days))
            return result if result else []
        except Exception as e:
            print(f"Error in get_login_frequency: {e}")
            return []
    
    @staticmethod
    def get_action_summary(user_id, days=30):
        query = """
        SELECT action_type, COUNT(*) as total
        FROM user_analytics 
        WHERE user_id = %s 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY action_type
        ORDER BY total DESC
        """
        try:
            result = db.fetch_query(query, (user_id, days))
            return result if result else []
        except Exception as e:
            print(f"Error in get_action_summary: {e}")
            return []

class FileAnalytics:
    def __init__(self, file_id=None, action_type=None, user_id=None, ip_address=None):
        self.file_id = file_id
        self.action_type = action_type
        self.user_id = user_id
        self.ip_address = ip_address
        self.id = None
        self.timestamp = None
    
    @staticmethod
    def record_action(file_id, action_type, user_id=None, ip_address=None):
        query = "INSERT INTO file_analytics (file_id, action_type, user_id, ip_address) VALUES (%s, %s, %s, %s)"
        params = (file_id, action_type, user_id, ip_address)
        cursor = db.execute_query(query, params)
        return cursor is not None
    
    @staticmethod
    def get_popular_files(user_id=None, limit=10):
        try:
            if user_id:
                query = """
                SELECT f.file_name, COUNT(fa.action_type) as access_count,
                       SUM(CASE WHEN fa.action_type = 'download' THEN 1 ELSE 0 END) as downloads
                FROM file_analytics fa
                JOIN files f ON fa.file_id = f.id
                WHERE f.user_id = %s
                GROUP BY fa.file_id, f.file_name
                ORDER BY access_count DESC
                LIMIT %s
                """
                result = db.fetch_query(query, (user_id, limit))
                return result if result else []
            else:
                query = """
                SELECT f.file_name, COUNT(fa.action_type) as access_count,
                       SUM(CASE WHEN fa.action_type = 'download' THEN 1 ELSE 0 END) as downloads
                FROM file_analytics fa
                JOIN files f ON fa.file_id = f.id
                GROUP BY fa.file_id, f.file_name
                ORDER BY access_count DESC
                LIMIT %s
                """
                result = db.fetch_query(query, (limit,))
                return result if result else []
        except Exception as e:
            print(f"Error in get_popular_files: {e}")
            return []
    
    @staticmethod
    def get_file_stats(file_id):
        query = """
        SELECT action_type, COUNT(*) as count
        FROM file_analytics 
        WHERE file_id = %s
        GROUP BY action_type
        """
        return db.fetch_query(query, (file_id,))

class StorageStats:
    def __init__(self, user_id=None, total_files=0, total_size=0):
        self.user_id = user_id
        self.total_files = total_files
        self.total_size = total_size
        self.id = None
        self.last_updated = None
    
    @staticmethod
    def update_user_storage(user_id):
        # Calculate current storage usage
        query = """
        SELECT COUNT(*) as file_count, COALESCE(SUM(s3_url), 0) as total_size
        FROM files 
        WHERE user_id = %s
        """
        result = db.fetch_one(query, (user_id,))
        
        if result:
            # Update or insert storage stats
            update_query = """
            INSERT INTO storage_stats (user_id, total_files, total_size)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            total_files = VALUES(total_files),
            total_size = VALUES(total_size),
            last_updated = CURRENT_TIMESTAMP
            """
            params = (user_id, result['file_count'], result['total_size'])
            cursor = db.execute_query(update_query, params)
            return cursor is not None
        return False
    
    @staticmethod
    def get_storage_usage(user_id):
        query = "SELECT * FROM storage_stats WHERE user_id = %s"
        try:
            result = db.fetch_one(query, (user_id,))
            return result
        except Exception as e:
            print(f"Error in get_storage_usage: {e}")
            return None
    
    @staticmethod
    def get_storage_trends(user_id, days=30):
        # This would require historical data - for now we'll return current stats
        query = """
        SELECT total_files, total_size, last_updated
        FROM storage_stats 
        WHERE user_id = %s
        """
        return db.fetch_query(query, (user_id,))
