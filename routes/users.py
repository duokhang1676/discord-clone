from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from datetime import datetime, timedelta
import secrets

# Khởi tạo Blueprint cho authentication
users_bp = Blueprint("users", __name__)

# MongoDB connection
db = get_db()
users_collection = db['users']
sessions_collection = db['sessions']

# Create index for username (unique)
try:
    users_collection.create_index("username", unique=True)
except:
    pass  # Index may already exist

@users_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username và password không được để trống'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username phải có ít nhất 3 ký tự'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password phải có ít nhất 6 ký tự'}), 400
        
        # Check if username already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username đã tồn tại'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Create user
        user = {
            'username': username,
            'password': hashed_password
        }
        
        result = users_collection.insert_one(user)
        
        return jsonify({
            'success': True,
            'message': 'Đăng ký thành công!',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f"Register error: {str(e)}")
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi đăng ký'}), 500

@users_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username và password không được để trống'}), 400
        
        # Find user
        user = users_collection.find_one({'username': username})
        
        if not user:
            return jsonify({'success': False, 'message': 'Username hoặc password không đúng'}), 401
        
        # Check password
        if not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Username hoặc password không đúng'}), 401
        
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Store session in MongoDB (for Safari iOS compatibility)
        sessions_collection.insert_one({
            'token': session_token,
            'user_id': str(user['_id']),
            'username': username,
            'created_at': datetime.utcnow()
        })
        
        # Also set Flask session (for backward compatibility with desktop browsers)
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        session['token'] = session_token
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công!',
            'username': user['username'],
            'session_token': session_token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi đăng nhập'}), 500

@users_bp.route('/logout', methods=['POST'])
def logout():
    # Remove token from MongoDB if present
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
        sessions_collection.delete_one({'token': token})
    
    # Clear Flask session
    session.clear()
    return jsonify({'success': True, 'message': 'Đăng xuất thành công'}), 200

@users_bp.route('/check-auth', methods=['GET'])
def check_auth():
    # Priority 1: Check Authorization header (for Safari iOS)
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
        
        # Look up token in MongoDB
        session_data = sessions_collection.find_one({'token': token})
        
        if session_data:
            return jsonify({
                'authenticated': True,
                'username': session_data['username']
            }), 200
    
    # Priority 2: Fallback to Flask session (for desktop browsers)
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username')
        }), 200
    
    return jsonify({'authenticated': False}), 200

@users_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Auth routes are working'}), 200
