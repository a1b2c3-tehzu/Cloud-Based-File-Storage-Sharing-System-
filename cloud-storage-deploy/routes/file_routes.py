from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.utils import secure_filename
from models.file_model import File
from models.folder_model import Folder
from models.db import db
from utils.s3_service import s3_service
from routes.auth_routes import login_required
import os
import shutil
from config import Config

file_bp = Blueprint('file', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@file_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    folder_id = request.args.get('folder_id')
    
    # Get files in current folder or root
    files = File.get_by_user(user_id, folder_id)
    print(f"Debug: Retrieved {len(files) if files else 0} files for user {user_id} in folder {folder_id}")
    
    # Get folder information
    current_folder = None
    breadcrumb = []
    folders = []
    
    if folder_id:
        current_folder = Folder.get_by_id(folder_id)
        if current_folder and current_folder['user_id'] == user_id:
            breadcrumb = Folder.get_folder_path(folder_id)
            folders = Folder.get_child_folders(folder_id, user_id)
        else:
            # Invalid folder, redirect to root
            return redirect(url_for('file.dashboard'))
    else:
        # Root folder
        folders = Folder.get_root_folders(user_id)
    
    return render_template('dashboard.html', 
                         files=files, 
                         current_folder=current_folder,
                         breadcrumb=breadcrumb,
                         folders=folders)

@file_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        valid_files = []
        user_id = session['user_id']
        
        # Get current folder
        folder_id = request.form.get('folder_id')
        if folder_id == '':
            folder_id = None
        
        # Validate folder ownership
        if folder_id and not Folder.folder_exists(folder_id, user_id):
            folder_id = None
        
        # Filter valid files
        for file in files:
            if file.filename != '' and allowed_file(file.filename):
                valid_files.append(file)
        
        print(f"Debug: Found {len(valid_files)} valid files out of {len(files)} total files")
        
        if not valid_files:
            flash('No valid files selected', 'error')
            return redirect(request.url)
        
        # Process multiple files
        uploaded_files = []
        failed_files = []
        
        for file in valid_files:
            try:
                filename = secure_filename(file.filename)
                print(f"Debug: Processing file: {filename}")
                
                # Create upload directories if they don't exist
                temp_dir = Config.UPLOAD_FOLDER
                local_dir = 'static/uploads'
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                    print(f"Debug: Created temp directory: {temp_dir}")
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir)
                    print(f"Debug: Created local directory: {local_dir}")
                
                # Get file size before saving
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)  # Reset file pointer
                
                # Save file temporarily
                temp_path = os.path.join(temp_dir, filename)
                file.save(temp_path)
                print(f"Debug: Saved file temporarily to: {temp_path}")
                
                # Try to upload to S3, but fallback to local storage if S3 fails
                try:
                    print(f"Debug: Attempting S3 upload for {filename}")
                    s3_result = s3_service.upload_file(temp_path, filename, user_id)
                    print(f"Debug: S3 upload result: {s3_result}")
                    
                    if s3_result['success']:
                        print(f"Debug: S3 upload successful for {filename}")
                        # Save file metadata to database
                        new_file = File(
                            user_id=user_id,
                            file_name=filename,
                            file_size=file_size,
                            folder_id=folder_id,
                            s3_key=s3_result['s3_key'],
                            s3_url=s3_result['s3_url']
                        )
                        
                        if new_file.create():
                            uploaded_files.append(filename)
                            print(f"Debug: Database entry created for {filename}")
                        else:
                            failed_files.append(filename)
                            print(f"Debug: Failed to create database entry for {filename}")
                    else:
                        print(f"Debug: S3 upload failed, using local storage for {filename}")
                        # Fallback to local storage
                        local_path = os.path.join(local_dir, filename)
                        # Copy from temp to local uploads
                        shutil.copy2(temp_path, local_path)
                        print(f"Debug: Copied file to local storage: {local_path}")
                        
                        local_url = f"/static/uploads/{filename}"
                        new_file = File(
                            user_id=user_id,
                            file_name=filename,
                            file_size=file_size,
                            folder_id=folder_id,
                            s3_key=f"local/{filename}",
                            s3_url=local_url
                        )
                        
                        if new_file.create():
                            uploaded_files.append(filename)
                            print(f"Debug: Local storage database entry created for {filename}")
                        else:
                            failed_files.append(filename)
                            print(f"Debug: Failed to create local storage database entry for {filename}")
                except Exception as e:
                    print(f"Debug: S3 Upload Exception for {filename}: {e}")
                    # Fallback to local storage
                    local_path = os.path.join(local_dir, filename)
                    # Copy from temp to local uploads
                    shutil.copy2(temp_path, local_path)
                    print(f"Debug: Exception fallback - copied file to local storage: {local_path}")
                    
                    local_url = f"/static/uploads/{filename}"
                    new_file = File(
                        user_id=user_id,
                        file_name=filename,
                        file_size=file_size,
                        folder_id=folder_id,
                        s3_key=f"local/{filename}",
                        s3_url=local_url
                    )
                    
                    if new_file.create():
                        uploaded_files.append(filename)
                        print(f"Debug: Exception fallback - database entry created for {filename}")
                    else:
                        failed_files.append(filename)
                        print(f"Debug: Exception fallback - failed to create database entry for {filename}")
                
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                failed_files.append(file.filename)
        
        # Show results
        if uploaded_files:
            if len(uploaded_files) == 1:
                flash(f'File uploaded successfully: {uploaded_files[0]}', 'success')
            else:
                flash(f'{len(uploaded_files)} files uploaded successfully!', 'success')
        
        if failed_files:
            flash(f'{len(failed_files)} files failed to upload: {", ".join(failed_files)}', 'error')
        
        # Redirect back to current folder
        redirect_url = url_for('file.dashboard')
        if folder_id:
            redirect_url = f"{redirect_url}?folder_id={folder_id}"
        return redirect(redirect_url)
    
    # GET request - show upload form
    folder_id = request.args.get('folder_id')
    return render_template('upload.html', folder_id=folder_id)

@file_bp.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    user_id = session['user_id']
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('file.dashboard'))
    
    # Get file details
    file_details = File.get_by_id(file_id)
    if file_details:
        # Check if it's a local file or S3 file
        if file_details['s3_key'].startswith('local/'):
            # Delete local file
            local_filename = file_details['s3_key'].replace('local/', '')
            local_path = os.path.join('static/uploads', local_filename)
            if os.path.exists(local_path):
                os.remove(local_path)
            
            # Delete from database
            if File.delete(file_id, user_id):
                flash('File deleted successfully!', 'success')
            else:
                flash('Database deletion failed', 'error')
        else:
            # Delete from S3
            try:
                s3_result = s3_service.delete_file(file_details['s3_key'])
                
                if s3_result['success']:
                    # Delete from database
                    if File.delete(file_id, user_id):
                        flash('File deleted successfully!', 'success')
                    else:
                        flash('File deleted from S3 but database deletion failed', 'error')
                else:
                    flash(f'Deletion failed: {s3_result["error"]}', 'error')
            except Exception as e:
                flash(f'Deletion failed: {str(e)}', 'error')
    else:
        flash('File not found', 'error')
    
    return redirect(url_for('file.dashboard'))

@file_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    user_id = session['user_id']
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('file.dashboard'))
    
    # Get file details
    file_details = File.get_by_id(file_id)
    if file_details:
        # Check if it's a local file or S3 file
        if file_details['s3_key'].startswith('local/'):
            # Local file download
            local_filename = file_details['s3_key'].replace('local/', '')
            local_path = os.path.join('static/uploads', local_filename)
            if os.path.exists(local_path):
                return send_file(local_path, as_attachment=True, download_name=file_details['file_name'])
            else:
                flash('Local file not found', 'error')
        else:
            # S3 file download
            try:
                s3_result = s3_service.generate_presigned_url(file_details['s3_key'])
                if s3_result['success']:
                    return redirect(s3_result['url'])
                else:
                    flash(f'Download failed: {s3_result["error"]}', 'error')
            except Exception as e:
                flash(f'Download failed: {str(e)}', 'error')
    else:
        flash('File not found', 'error')
    
    return redirect(url_for('file.dashboard'))
