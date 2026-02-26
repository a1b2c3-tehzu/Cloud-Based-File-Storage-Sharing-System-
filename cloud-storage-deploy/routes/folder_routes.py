from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.file_model import File
from models.folder_model import Folder
from routes.auth_routes import login_required

folder_bp = Blueprint('folder', __name__)

@folder_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    user_id = session['user_id']
    folder_name = request.form.get('folder_name')
    parent_id = request.form.get('parent_id')
    
    if not folder_name:
        flash('Folder name is required', 'error')
        return redirect(request.referrer or url_for('file.dashboard'))
    
    # Validate parent folder
    if parent_id == '':
        parent_id = None
    elif parent_id and not Folder.folder_exists(parent_id, user_id):
        parent_id = None
    
    # Check if folder name already exists in parent
    existing_folders = Folder.get_child_folders(parent_id, user_id) if parent_id else Folder.get_root_folders(user_id)
    for folder in existing_folders:
        if folder['name'].lower() == folder_name.lower():
            flash('A folder with this name already exists', 'error')
            return redirect(request.referrer or url_for('file.dashboard'))
    
    # Create folder
    new_folder = Folder(user_id=user_id, name=folder_name, parent_id=parent_id)
    if new_folder.create():
        flash(f'Folder "{folder_name}" created successfully', 'success')
    else:
        flash('Failed to create folder', 'error')
    
    # Redirect back to parent folder
    redirect_url = url_for('file.dashboard')
    if parent_id:
        redirect_url = f"{redirect_url}?folder_id={parent_id}"
    return redirect(redirect_url)

@folder_bp.route('/move_to_folder/<int:file_id>', methods=['POST'])
@login_required
def move_to_folder(file_id):
    user_id = session['user_id']
    target_folder_id = request.form.get('target_folder_id')
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(request.referrer or url_for('file.dashboard'))
    
    # Validate target folder
    if target_folder_id == '':
        target_folder_id = None
    elif target_folder_id and not Folder.folder_exists(target_folder_id, user_id):
        flash('Invalid target folder', 'error')
        return redirect(request.referrer or url_for('file.dashboard'))
    
    # Move file
    if File.move_to_folder(file_id, target_folder_id, user_id):
        flash('File moved successfully', 'success')
    else:
        flash('Failed to move file', 'error')
    
    # Redirect to target folder
    redirect_url = url_for('file.dashboard')
    if target_folder_id:
        redirect_url = f"{redirect_url}?folder_id={target_folder_id}"
    return redirect(redirect_url)

@folder_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    user_id = session['user_id']
    
    # Verify folder ownership
    folder = Folder.get_by_id(folder_id)
    if not folder or folder['user_id'] != user_id:
        flash('Unauthorized access', 'error')
        return redirect(request.referrer or url_for('file.dashboard'))
    
    # Delete folder (moves contents to root)
    if Folder.delete(folder_id, user_id):
        flash(f'Folder "{folder["name"]}" deleted. Contents moved to root.', 'success')
    else:
        flash('Failed to delete folder', 'error')
    
    return redirect(url_for('file.dashboard'))

@folder_bp.route('/api/folder_tree')
@login_required
def folder_tree_api():
    """API endpoint to get folder tree for navigation"""
    user_id = session['user_id']
    tree = Folder.get_folder_tree(user_id)
    return jsonify(tree)
