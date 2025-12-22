from flask import Flask
from flask_cors import CORS
from routes.users import users_bp
from datetime import timedelta
import secrets

# Tạo ứng dụng Flask
app = Flask(__name__)

# Cấu hình session
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Enable CORS
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://localhost:3000", "https://192.168.1.6:3000"])

# Đăng ký các Blueprint với prefix /api
app.register_blueprint(users_bp, url_prefix="/api")

@app.route("/")
def index():
    """
    Route kiểm tra server.
    """
    return "Parking Management API is running!", 200

# Điểm khởi chạy server
if __name__ == "__main__":
    print("🔐 Auth Server starting...")
    print("📡 Listening on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
