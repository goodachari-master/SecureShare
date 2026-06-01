from flask import Blueprint, request, jsonify
from auth.session_store import SessionManager
from database.db_manager import DatabaseManager
from datetime import datetime
import logging

bp = Blueprint('notifications', __name__, url_prefix='/api')
db_manager = DatabaseManager()
logger = logging.getLogger(__name__)

@bp.route('/notifications/summary', methods=['GET'])
def get_notification_summary():
    """Get both unread count and latest notifications in one request"""
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        # 1. Get unread file count (for the badge)
        unread_count_res = db_manager.fetch_one("""
            SELECT COUNT(*) as count FROM files_metadata 
            WHERE recipient_id = %s AND is_read = FALSE AND is_deleted = FALSE
        """, (user['user_id'],))
        
        # 2. Get latest notifications (for the dropdown)
        limit = request.args.get('limit', 10, type=int)
        notifications = db_manager.fetch_all("""
            SELECT n.*, u.username as from_username
            FROM notifications n
            JOIN users u ON n.from_user_id = u.user_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
        """, (user['user_id'], limit))
        
        return jsonify({
            'success': True, 
            'data': {
                'count': unread_count_res['count'],
                'notifications': notifications
            }
        })
    except Exception as e:
        logger.error(f"Get notification summary error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        limit = request.args.get('limit', 50, type=int)
        
        notifications = db_manager.fetch_all("""
            SELECT n.*, u.username as from_username
            FROM notifications n
            JOIN users u ON n.from_user_id = u.user_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
        """, (user['user_id'], limit))
        
        return jsonify({'success': True, 'data': notifications})
    
    except Exception as e:
        logger.error(f"Get notifications error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/notifications/unread/count', methods=['GET'])
def get_unread_count():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        # Count unread files shared with the user instead of notification entries
        result = db_manager.fetch_one("""
            SELECT COUNT(*) as count FROM files_metadata 
            WHERE recipient_id = %s AND is_read = FALSE AND is_deleted = FALSE
        """, (user['user_id'],))
        
        return jsonify({'success': True, 'data': {'count': result['count']}})
    
    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/notifications/mark-read', methods=['POST'])
def mark_notification_read():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        if notification_id:
            db_manager.update('notifications',
                {'is_read': True, 'read_at': datetime.now()},
                'notification_id = %s AND user_id = %s',
                [notification_id, user['user_id']])
        else:
            # Mark all as read
            db_manager.update('notifications',
                {'is_read': True, 'read_at': datetime.now()},
                'user_id = %s AND is_read = FALSE',
                [user['user_id']])
        
        return jsonify({'success': True, 'message': 'Notifications marked as read'})
    
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500