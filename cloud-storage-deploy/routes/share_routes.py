from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.share_model import ShareLink
from models.file_model import File
from models.db import db
from utils.s3_service import s3_service
from routes.auth_routes import login_required
from config import Config

share_bp = Blueprint('share', __name__)

@share_bp.route('/generate-share/<int:file_id>')
@login_required
def generate_share(file_id):
    user_id = session['user_id']
    
    # Verify file ownership
    file_owner = File.get_file_owner(file_id)
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('file.dashboard'))
    
    # Check if file exists
    if not File.file_exists(file_id):
        flash('File not found', 'error')
        return redirect(url_for('file.dashboard'))
    
    # Generate share link
    share_link = ShareLink(file_id=file_id)
    if share_link.create(Config.DEFAULT_SHARE_EXPIRY_HOURS):
        share_url = url_for('share.access_shared_file', token=share_link.token, _external=True)
        flash(f'Share link generated! Link expires in {Config.DEFAULT_SHARE_EXPIRY_HOURS} hours.', 'success')
        return render_template('share.html', share_url=share_url, expiry_date=share_link.expiry_date)
    else:
        flash('Failed to generate share link', 'error')
        return redirect(url_for('file.dashboard'))

@share_bp.route('/share/<token>')
def access_shared_file(token):
    # Validate token
    file_info = ShareLink.get_file_info(token)
    
    if not file_info:
        flash('Invalid or expired share link', 'error')
        return render_template('error.html', message='The share link you accessed is invalid or has expired.')
    
    # Check if it's a local file or S3 file
    if file_info['s3_key'].startswith('local/'):
        # Local file download
        local_filename = file_info['s3_key'].replace('local/', '')
        download_url = f"/static/uploads/{local_filename}"
        return render_template('share.html', 
                             file_info=file_info, 
                             download_url=download_url,
                             is_shared_access=True)
    else:
        # S3 file download
        try:
            s3_result = s3_service.generate_presigned_url(file_info['s3_key'])
            
            if s3_result['success']:
                download_url = s3_result['url']
                return render_template('share.html', 
                                     file_info=file_info, 
                                     download_url=download_url,
                                     is_shared_access=True)
            else:
                flash('Failed to generate download link', 'error')
                return render_template('error.html', message='Unable to generate download link for this file.')
        except Exception as e:
            flash('Failed to generate download link', 'error')
            return render_template('error.html', message='Unable to generate download link for this file.')

@share_bp.route('/share')
@login_required
def share_page():
    # This can be used to display all shared links for the user
    return render_template('share.html')

# Helper function to clean expired links
def cleanup_expired_links():
    ShareLink.delete_expired()
