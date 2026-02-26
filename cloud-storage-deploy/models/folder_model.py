from models.db import db
import datetime

class Folder:
    def __init__(self, user_id=None, name=None, parent_id=None):
        self.user_id = user_id
        self.name = name
        self.parent_id = parent_id
        self.id = None
        self.created_at = None
    
    def create(self):
        query = "INSERT INTO folders (user_id, name, parent_id) VALUES (%s, %s, %s)"
        params = (self.user_id, self.name, self.parent_id)
        
        cursor = db.execute_query(query, params)
        if cursor:
            self.id = cursor.lastrowid
            return True
        return False
    
    @staticmethod
    def get_by_user(user_id):
        query = "SELECT * FROM folders WHERE user_id = %s ORDER BY name"
        result = db.fetch_query(query, (user_id,))
        return result if result else []
    
    @staticmethod
    def get_by_id(folder_id):
        query = "SELECT * FROM folders WHERE id = %s"
        result = db.fetch_one(query, (folder_id,))
        return result
    
    @staticmethod
    def get_root_folders(user_id):
        query = "SELECT * FROM folders WHERE user_id = %s AND parent_id IS NULL ORDER BY name"
        result = db.fetch_query(query, (user_id,))
        return result if result else []
    
    @staticmethod
    def get_child_folders(parent_id, user_id):
        query = "SELECT * FROM folders WHERE parent_id = %s AND user_id = %s ORDER BY name"
        result = db.fetch_query(query, (parent_id, user_id))
        return result if result else []
    
    @staticmethod
    def get_folder_path(folder_id):
        """Get the full path of a folder (breadcrumb trail)"""
        path = []
        current_folder_id = folder_id
        
        while current_folder_id:
            query = "SELECT id, name, parent_id FROM folders WHERE id = %s"
            folder = db.fetch_one(query, (current_folder_id,))
            if folder:
                path.append(folder)
                current_folder_id = folder['parent_id']
            else:
                break
        
        return list(reversed(path))  # Reverse to get root-to-current order
    
    @staticmethod
    def delete(folder_id, user_id):
        """Delete a folder and move all files to root"""
        try:
            # Move all files in this folder to root (folder_id = NULL)
            update_query = "UPDATE files SET folder_id = NULL WHERE folder_id = %s AND user_id = %s"
            db.execute_query(update_query, (folder_id, user_id))
            
            # Move all subfolders to root
            update_subfolders = "UPDATE folders SET parent_id = NULL WHERE parent_id = %s AND user_id = %s"
            db.execute_query(update_subfolders, (folder_id, user_id))
            
            # Delete the folder
            delete_query = "DELETE FROM folders WHERE id = %s AND user_id = %s"
            cursor = db.execute_query(delete_query, (folder_id, user_id))
            return cursor is not None
        except Exception as e:
            print(f"Error deleting folder: {e}")
            return False
    
    @staticmethod
    def folder_exists(folder_id, user_id):
        query = "SELECT id FROM folders WHERE id = %s AND user_id = %s"
        result = db.fetch_one(query, (folder_id, user_id))
        return result is not None
    
    @staticmethod
    def get_folder_tree(user_id):
        """Get folder tree structure for navigation"""
        folders = Folder.get_by_user(user_id)
        tree = {}
        
        # Create a mapping of folders
        folder_map = {}
        for folder in folders:
            folder_map[folder['id']] = {
                'id': folder['id'],
                'name': folder['name'],
                'parent_id': folder['parent_id'],
                'children': []
            }
        
        # Build tree structure
        for folder_id, folder_data in folder_map.items():
            parent_id = folder_data['parent_id']
            if parent_id is None:
                tree[folder_id] = folder_data
            elif parent_id in folder_map:
                folder_map[parent_id]['children'].append(folder_data)
        
        return tree
    
    @staticmethod
    def get_folder_contents(folder_id, user_id):
        """Get all files and subfolders in a folder"""
        # Get files in folder
        files_query = "SELECT * FROM files WHERE folder_id = %s AND user_id = %s ORDER BY file_name"
        files = db.fetch_query(files_query, (folder_id, user_id))
        
        # Get subfolders
        subfolders_query = "SELECT * FROM folders WHERE parent_id = %s AND user_id = %s ORDER BY name"
        subfolders = db.fetch_query(subfolders_query, (folder_id, user_id))
        
        return {
            'files': files if files else [],
            'subfolders': subfolders if subfolders else []
        }
