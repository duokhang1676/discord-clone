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
        # Check authentication (session or token)
        if 'user_id' not in session:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False, 
                    'message': 'Unauthorized'
                }), 401
            
            # Verify token if provided
            token = auth_header.replace('Bearer ', '')
            if session.get('token') != token:
                return jsonify({
                    'success': False,
                    'message': 'Invalid token'
                }), 401
        
        # Get last 100 messages, sorted by timestamp
        messages = list(db.messages.find()
            .sort('timestamp', -1)
            .limit(100))
        
        # Reverse to show oldest first
        messages.reverse()
        
        # Convert ObjectId to string for JSON serialization
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/messages', methods=['POST'])
def save_message():
    """Save new message from voice server"""
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
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'created_at': datetime.utcnow()
        }
        
        result = db.messages.insert_one(message_doc)
        
        return jsonify({
            'success': True,
            'message_id': str(result.inserted_id)
        })
        
    except Exception as e:
        print(f"Error saving message: {str(e)}")
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
        
        return jsonify({
            'success': True,
            'deleted_count': result.deleted_count
        })
        
    except Exception as e:
        print(f"Error clearing messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
