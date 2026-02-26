from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.analytics_model import ShareAnalytics, UserAnalytics, FileAnalytics, StorageStats
from models.file_model import File
from models.share_model import ShareLink
from routes.auth_routes import login_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def analytics_dashboard():
    user_id = session['user_id']
    
    try:
        # Get user activity summary
        user_activity = UserAnalytics.get_action_summary(user_id) or []
        login_frequency = UserAnalytics.get_login_frequency(user_id) or []
        
        # Get storage stats
        storage_stats = StorageStats.get_storage_usage(user_id)
        
        # Get popular files
        popular_files = FileAnalytics.get_popular_files(user_id) or []
        
        # Get upload patterns (last 30 days)
        upload_stats = UserAnalytics.get_user_activity(user_id)
        upload_pattern = [stat for stat in upload_stats if upload_stats and stat.get('action_type') == 'upload']
        
    except Exception as e:
        # Handle case where analytics tables don't exist yet
        print(f"Analytics error: {e}")
        user_activity = []
        login_frequency = []
        storage_stats = None
        popular_files = []
        upload_pattern = []
    
    return render_template('analytics.html', 
                         user_activity=user_activity,
                         login_frequency=login_frequency,
                         storage_stats=storage_stats,
                         popular_files=popular_files,
                         upload_pattern=upload_pattern)

@analytics_bp.route('/analytics/storage')
@login_required
def storage_analytics():
    user_id = session['user_id']
    
    # Update storage stats
    StorageStats.update_user_storage(user_id)
    
    # Get storage usage
    storage_stats = StorageStats.get_storage_usage(user_id)
    
    # Get storage trends
    storage_trends = StorageStats.get_storage_trends(user_id)
    
    return render_template('storage_analytics.html',
                         storage_stats=storage_stats,
                         storage_trends=storage_trends)

@analytics_bp.route('/analytics/share-stats/<token>')
@login_required
def share_analytics(token):
    user_id = session['user_id']
    
    # Verify ownership
    share_info = ShareLink.get_by_token(token)
    if not share_info:
        flash('Share link not found', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))
    
    file_owner = File.get_file_owner(share_info['file_id'])
    if file_owner != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))
    
    # Get share statistics
    share_stats = ShareAnalytics.get_share_stats(share_info['id'])
    access_timeline = ShareAnalytics.get_access_timeline(share_info['id'])
    
    return render_template('share_analytics.html',
                         share_info=share_info,
                         share_stats=share_stats,
                         access_timeline=access_timeline)

@analytics_bp.route('/analytics/api/storage-chart')
@login_required
def storage_chart_api():
    user_id = session['user_id']
    storage_stats = StorageStats.get_storage_usage(user_id)
    
    if storage_stats:
        # Calculate percentage of usage (assuming 1GB limit for demo)
        total_limit = 1024 * 1024 * 1024  # 1GB in bytes
        used_percentage = (storage_stats['total_size'] / total_limit) * 100
        
        return jsonify({
            'used': storage_stats['total_size'],
            'files': storage_stats['total_files'],
            'percentage': round(used_percentage, 2),
            'limit': total_limit
        })
    
    return jsonify({'used': 0, 'files': 0, 'percentage': 0, 'limit': 1024*1024*1024})

@analytics_bp.route('/analytics/api/activity-chart')
@login_required
def activity_chart_api():
    user_id = session['user_id']
    days = request.args.get('days', 30, type=int)
    
    user_activity = UserAnalytics.get_action_summary(user_id, days)
    
    # Format data for chart
    chart_data = []
    for activity in user_activity:
        chart_data.append({
            'action': activity['action_type'],
            'count': activity['total']
        })
    
    return jsonify(chart_data)

@analytics_bp.route('/analytics/api/popular-files')
@login_required
def popular_files_api():
    user_id = session['user_id']
    popular_files = FileAnalytics.get_popular_files(user_id, 10)
    
    return jsonify(popular_files)

# Helper function to record analytics
def record_user_action(user_id, action_type, details=None):
    UserAnalytics.record_action(user_id, action_type, details)

def record_file_action(file_id, action_type, user_id=None, ip_address=None):
    FileAnalytics.record_action(file_id, action_type, user_id, ip_address)

def record_share_access(share_link_id, ip_address, user_agent):
    ShareAnalytics.record_access(share_link_id, ip_address, user_agent)
