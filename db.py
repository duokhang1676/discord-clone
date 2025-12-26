from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

def get_db():
    """
    Kết nối đến MongoDB và trả về đối tượng database.
    """
    # Load biến môi trường từ file .env
    load_dotenv()

    # Lấy connection string từ biến môi trường
    uri = os.getenv("MONGO_URI")

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    db = client["discord_clone"]
    return db


db = get_db()

# Create sessions collection with TTL index for automatic expiration
sessions_collection = db['sessions']
try:
    # TTL index: auto-delete sessions after 24 hours (86400 seconds)
    sessions_collection.create_index('created_at', expireAfterSeconds=86400)
    print("✅ Sessions collection with TTL index created")
except Exception as e:
    print(f"⚠️ Sessions index warning: {str(e)}")
