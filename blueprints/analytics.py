from flask import Blueprint, jsonify, request, session
import logging
import time
from datetime import datetime

# Analytics blueprint
analytics_bp = Blueprint('analytics', __name__)

# In-memory storage for basic analytics
# In a production environment, this would be stored in a database
PAGE_VIEWS = {}
SEARCH_ANALYTICS = []
UPLOAD_ANALYTICS = []
USER_ANALYTICS = {}
EVENT_ANALYTICS = []

@analytics_bp.route('/api/analytics/record-view', methods=['POST'])
def record_view():
    """Record a page view for analytics"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    page = data.get('page')
    
    if not page:
        return jsonify({'error': 'Page not specified'}), 400
        
    # Record the page view
    if page in PAGE_VIEWS:
        PAGE_VIEWS[page] += 1
    else:
        PAGE_VIEWS[page] = 1
        
    # Record user info if available
    user_id = session.get('google_id')
    if user_id:
        if user_id not in USER_ANALYTICS:
            USER_ANALYTICS[user_id] = {
                'email': session.get('email', 'unknown'),
                'name': session.get('name', 'unknown'),
                'first_seen': datetime.now().isoformat(),
                'page_views': {}
            }
            
        user_data = USER_ANALYTICS[user_id]
        if page in user_data['page_views']:
            user_data['page_views'][page] += 1
        else:
            user_data['page_views'][page] = 1
        user_data['last_seen'] = datetime.now().isoformat()
    
    return jsonify({'success': True})

@analytics_bp.route('/api/analytics/record-search', methods=['POST'])
def record_search():
    """Record search parameters for analytics"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    search_params = data.get('params', {})
    results_count = data.get('results_count', 0)
    
    search_record = {
        'timestamp': datetime.now().isoformat(),
        'params': search_params,
        'results_count': results_count,
        'user_id': session.get('google_id'),
        'user_email': session.get('email')
    }
    
    SEARCH_ANALYTICS.append(search_record)
    return jsonify({'success': True})

@analytics_bp.route('/api/analytics/record-upload', methods=['POST'])
def record_upload():
    """Record file upload for analytics"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    file_info = data.get('file_info', {})
    
    upload_record = {
        'timestamp': datetime.now().isoformat(),
        'file_info': file_info,
        'user_id': session.get('google_id'),
        'user_email': session.get('email')
    }
    
    UPLOAD_ANALYTICS.append(upload_record)
    return jsonify({'success': True})

@analytics_bp.route('/api/analytics/summary', methods=['GET'])
def analytics_summary():
    """Get analytics summary - admin only"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 403
        
    summary = {
        'page_views': PAGE_VIEWS,
        'user_count': len(USER_ANALYTICS),
        'search_count': len(SEARCH_ANALYTICS),
        'upload_count': len(UPLOAD_ANALYTICS),
        'event_count': len(EVENT_ANALYTICS),
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(summary)

@analytics_bp.route('/api/analytics/record-event', methods=['POST'])
def record_event():
    """Record a custom event for analytics"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    event_type = data.get('event_type')
    event_data = data.get('event_data', {})
    
    if not event_type:
        return jsonify({'error': 'Event type not specified'}), 400
        
    # Record the event
    event_record = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'event_data': event_data,
        'user_id': session.get('google_id'),
        'user_email': session.get('email')
    }
    
    EVENT_ANALYTICS.append(event_record)
    return jsonify({'success': True})
