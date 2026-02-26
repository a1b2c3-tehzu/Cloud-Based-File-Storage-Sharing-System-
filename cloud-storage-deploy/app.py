from flask import Flask, render_template
from models.db import db
from routes.auth_routes import auth_bp
from routes.file_routes import file_bp
from routes.share_routes import share_bp
from routes.analytics_routes import analytics_bp
from routes.folder_routes import folder_bp
from routes.preview_routes import preview_bp
from config import config
import os

def create_app(config_name=None):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app.config.from_object(config[config_name])
    
    # Initialize database
    if not db.connect():
        print("Failed to connect to database")
        return None
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(file_bp, url_prefix='/')
    app.register_blueprint(share_bp, url_prefix='/')
    app.register_blueprint(analytics_bp, url_prefix='/')
    app.register_blueprint(folder_bp, url_prefix='/')
    app.register_blueprint(preview_bp, url_prefix='/')
    
    # Add template context processor
    @app.context_processor
    def inject_helpers():
        def getFileIcon(filename):
            extension = filename.split('.').pop().lower()
            icon_map = {
                'pdf': 'bi-file-earmark-pdf text-danger',
                'doc': 'bi-file-earmark-word text-primary',
                'docx': 'bi-file-earmark-word text-primary',
                'xls': 'bi-file-earmark-excel text-success',
                'xlsx': 'bi-file-earmark-excel text-success',
                'ppt': 'bi-file-earmark-powerpoint text-warning',
                'pptx': 'bi-file-earmark-powerpoint text-warning',
                'jpg': 'bi-file-earmark-image text-info',
                'jpeg': 'bi-file-earmark-image text-info',
                'png': 'bi-file-earmark-image text-info',
                'gif': 'bi-file-earmark-image text-info',
                'zip': 'bi-file-earmark-archive text-secondary',
                'rar': 'bi-file-earmark-archive text-secondary',
                'txt': 'bi-file-earmark-text text-muted'
            }
            return icon_map.get(extension, 'bi-file-earmark text-muted')
        
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
        
        return dict(getFileIcon=getFileIcon, File={'format_file_size': format_file_size})
    
    # Root route - redirect to login or dashboard
    @app.route('/')
    def index():
        from flask import session
        if 'user_id' in session:
            from flask import redirect, url_for
            return redirect(url_for('file.dashboard'))
        else:
            from flask import redirect, url_for
            return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', message='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.disconnect()
        return render_template('error.html', message='Internal server error'), 500
    
    # Cleanup on app shutdown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass  # Keep connection alive
    
    return app

if __name__ == '__main__':
    app = create_app()
    if app:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True  # Enable debug mode
        )
    else:
        print("Failed to create application")
