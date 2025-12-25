from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from bson import ObjectId

messages_bp = Blueprint('messages', __name__)

# Inject db from app.py
db = None

def init_messages_routes(database):
    global db
    db = database

@messages_bp.route('/messages', methods=['GET'])
def get_messages():
    """Get message history (last 100 messages)"""
    try:
        # Get last 100 messages, sorted by timestamp
        messages = list(db.messages.find(
            {},
            {'_id': 0}  # Exclude MongoDB _id field
        ).sort('timestamp', -1).limit(100))
        
        # Reverse to show oldest first
        messages.reverse()
        
        print(f'📥 Retrieved {len(messages)} messages from database')
        
        return jsonify({
            'success': True,
            'messages': messages
        }), 200
        
    except Exception as e:
        print(f'❌ Error getting messages: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/messages', methods=['POST'])
def save_message():
    """Save new message from voice server (text or image)"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('message') or not data.get('username'):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        message_doc = {
            'user_id': data.get('user_id'),
            'username': data.get('username'),
            'message': data.get('message'),
            'type': data.get('type', 'text'),  # 'text' or 'image'
            'imageUrl': data.get('imageUrl'),   # Cloudinary URL or None
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat())
        }
        
        result = db.messages.insert_one(message_doc)
        
        # Log with appropriate message type
        message_type = message_doc['type']
        log_msg = f"[{message_type.upper()}]" if message_type == 'image' else message_doc['message']
        print(f'💾 Saved message from {data.get("username")}: {log_msg}')
        
        return jsonify({
            'success': True,
            'message': 'Message saved',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f'❌ Error saving message: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/messages/clear', methods=['DELETE'])
def clear_messages():
    """Clear all messages (authenticated users only)"""
    try:
        # Check authentication
        if 'user_id' not in session:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'message': 'Unauthorized'
                }), 401
        
        result = db.messages.delete_many({})
        
        print(f'🗑️ Cleared {result.deleted_count} messages by user {session.get("user_id")}')
        
        return jsonify({
            'success': True,
            'deleted_count': result.deleted_count
        }), 200
        
    except Exception as e:
        print(f'❌ Error clearing messages: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/messages/health', methods=['GET'])
def health_check():
    """Check if messages API is working"""
    try:
        count = db.messages.count_documents({})
        return jsonify({
            'success': True,
            'status': 'healthy',
            'total_messages': count
        }), 200
    except Exception as e:
        print(f'❌ Health check failed: {str(e)}')
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
