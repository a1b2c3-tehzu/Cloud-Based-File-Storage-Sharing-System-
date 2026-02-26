from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.utils import secure_filename
from models.file_model import File
from models.db import db
from utils.s3_service import s3_service
from routes.auth_routes import login_required
import os
import mimetypes
from config import Config

preview_bp = Blueprint('preview', __name__)

def get_file_type(filename):
    """Determine file type from filename"""
    extension = filename.split('.').pop().lower()
    
    # Image files
    image_types = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']
    if extension in image_types:
        return 'image'
    
    # Text files
    text_types = ['txt', 'md', 'json', 'xml', 'csv', 'log', 'ini', 'cfg', 'conf']
    if extension in text_types:
        return 'text'
    
    # Code files
    code_types = ['py', 'js', 'html', 'css', 'php', 'java', 'cpp', 'c', 'h', 'sql', 'sh', 'bat']
    if extension in code_types:
        return 'code'
    
    # PDF files
    if extension == 'pdf':
        return 'pdf'
    
    # Document files (that we can't preview directly)
    doc_types = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
    if extension in doc_types:
        return 'document'
    
    # Archive files
    archive_types = ['zip', 'rar', '7z', 'tar', 'gz']
    if extension in archive_types:
        return 'archive'
    
    # Video files
    video_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
    if extension in video_types:
        return 'video'
    
    # Audio files
    audio_types = ['mp3', 'wav', 'ogg', 'flac', 'aac']
    if extension in audio_types:
        return 'audio'
    
    return 'unknown'

def get_file_content(file_path, file_type):
    """Get file content for preview"""
    try:
        if file_type in ['text', 'code']:
            # For text and code files, read the content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return content
        elif file_type == 'image':
            # For images, we'll handle in the template
            return None
        else:
            return None
    except Exception as e:
        print(f"Error reading file content: {e}")
        return None

@preview_bp.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    user_id = session['user_id']
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('file.dashboard'))
    
    # Get file details
    file_details = File.get_by_id(file_id)
    if not file_details:
        flash('File not found', 'error')
        return redirect(url_for('file.dashboard'))
    
    file_type = get_file_type(file_details['file_name'])
    file_size = file_details.get('file_size', 0)
    
    # Debug information
    print(f"Debug: Preview request for file_id={file_id}")
    print(f"Debug: File details: {file_details}")
    print(f"Debug: File type: {file_type}")
    print(f"Debug: S3 key: {file_details['s3_key']}")
    
    # Handle different file types
    if file_type == 'image':
        # For images, render the preview template with image path
        if file_details['s3_key'].startswith('local/'):
            # Local file
            local_filename = file_details['s3_key'].replace('local/', '')
            file_path = f"/static/uploads/{local_filename}"
            full_path = os.path.join('static/uploads', local_filename)
            print(f"Debug: Image file path: {full_path}")
            print(f"Debug: Image file exists: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                file_size_actual = os.path.getsize(full_path)
                print(f"Debug: Image file size: {file_size_actual} bytes")
                if file_size_actual > 0:
                    return render_template('preview.html', 
                                         file=file_details,
                                         file_path=file_path,
                                         file_type=file_type,
                                         file_size=file_size)
                else:
                    flash('Image file is empty', 'error')
                    return redirect(url_for('file.dashboard'))
            else:
                flash('File not found', 'error')
                return redirect(url_for('file.dashboard'))
        else:
            # S3 file - generate presigned URL for embedding
            try:
                s3_result = s3_service.generate_presigned_url(file_details['s3_key'])
                if s3_result['success']:
                    return render_template('preview.html', 
                                         file=file_details,
                                         file_url=s3_result['url'],
                                         file_type=file_type,
                                         file_size=file_size)
                else:
                    flash('Failed to generate preview URL', 'error')
                    return redirect(url_for('file.dashboard'))
            except Exception as e:
                flash(f'Preview failed: {str(e)}', 'error')
                return redirect(url_for('file.dashboard'))
    
    elif file_type in ['text', 'code']:
        # For text and code files, read content
        if file_details['s3_key'].startswith('local/'):
            # Local file
            local_filename = file_details['s3_key'].replace('local/', '')
            file_path = os.path.join('static/uploads', local_filename)
            if os.path.exists(file_path):
                content = get_file_content(file_path, file_type)
                if content is not None:
                    # Ensure content is not empty
                    if not content.strip():
                        content = "[File is empty or contains no readable content]"
                    return render_template('preview.html', 
                                         file=file_details,
                                         content=content,
                                         file_type=file_type,
                                         file_size=file_size)
                else:
                    flash('Failed to read file content', 'error')
                    return redirect(url_for('file.dashboard'))
            else:
                flash('File not found', 'error')
                return redirect(url_for('file.dashboard'))
        else:
            # S3 file - download temporarily for preview
            try:
                # This would require downloading from S3 first
                # For now, suggest download
                flash('Text files from S3 cannot be previewed directly. Please download to view.', 'info')
                return redirect(url_for('file.download_file', file_id=file_id))
            except Exception as e:
                flash(f'Preview failed: {str(e)}', 'error')
                return redirect(url_for('file.dashboard'))
    
    elif file_type == 'pdf':
        # For PDF files, we'll embed them
        if file_details['s3_key'].startswith('local/'):
            # Local file
            local_filename = file_details['s3_key'].replace('local/', '')
            file_path = os.path.join('static/uploads', local_filename)
            if os.path.exists(file_path):
                return render_template('preview.html', 
                                     file=file_details,
                                     file_path=f"/static/uploads/{local_filename}",
                                     file_type=file_type,
                                     file_size=file_size)
            else:
                flash('File not found', 'error')
                return redirect(url_for('file.dashboard'))
        else:
            # S3 file - generate presigned URL for embedding
            try:
                s3_result = s3_service.generate_presigned_url(file_details['s3_key'])
                if s3_result['success']:
                    return render_template('preview.html', 
                                         file=file_details,
                                         file_url=s3_result['url'],
                                         file_type=file_type,
                                         file_size=file_size)
                else:
                    flash('Failed to generate preview URL', 'error')
                    return redirect(url_for('file.dashboard'))
            except Exception as e:
                flash(f'Preview failed: {str(e)}', 'error')
                return redirect(url_for('file.dashboard'))
    
    else:
        # For other file types, show download suggestion
        return render_template('preview.html', 
                             file=file_details,
                             file_type=file_type,
                             file_size=file_size)

@preview_bp.route('/test-files')
@login_required
def test_files():
    """Test route to check available files"""
    user_id = session['user_id']
    files = File.get_by_user(user_id)

    file_info = []
    for file in files:
        file_path = None
        exists = False
        file_size = 0
        if file['s3_key'].startswith('local/'):
            local_filename = file['s3_key'].replace('local/', '')
            file_path = os.path.join('static/uploads', local_filename)
            exists = os.path.exists(file_path)
            if exists:
                file_size = os.path.getsize(file_path)

        file_info.append({
            'id': file['id'],
            'name': file['file_name'],
            's3_key': file['s3_key'],
            'file_path': file_path,
            'exists': exists,
            'file_size': file_size,
            'type': get_file_type(file['file_name'])
        })

    return jsonify({'files': file_info})

@preview_bp.route('/test-image/<filename>')
def test_image(filename):
    """Test route to serve images directly"""
    from flask import send_from_directory, current_app
    print(f"Debug: Serving image: {filename}")
    print(f"Debug: Upload folder: {current_app.static_folder}")
    return send_from_directory('static/uploads', filename)

@preview_bp.route('/test-static')
def test_static():
    """Test if static files are accessible"""
    from flask import url_for
    return jsonify({
        'static_url': url_for('static', filename='uploads/test_image.jpg'),
        'test_image_url': url_for('preview_bp.test_image', filename='test_image.jpg')
    })

@preview_bp.route('/api/preview-info/<int:file_id>')
@login_required
def preview_info(file_id):
    """API endpoint to get file preview information"""
    user_id = session['user_id']
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get file details
    file_details = File.get_by_id(file_id)
    if not file_details:
        return jsonify({'error': 'File not found'}), 404
    
    file_type = get_file_type(file_details['file_name'])
    file_size = file_details.get('file_size', 0)
    
    # Determine if preview is available
    preview_available = file_type in ['image', 'text', 'code', 'pdf']
    
    response_data = {
        'file_id': file_id,
        'file_name': file_details['file_name'],
        'file_type': file_type,
        'file_size': file_size,
        'preview_available': preview_available,
        'created_at': file_details['created_at'].isoformat() if file_details['created_at'] else None
    }
    
    return jsonify(response_data)
