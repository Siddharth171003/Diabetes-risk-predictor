from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from utils.db import get_db

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc['username']
        self.email = user_doc['email']
        self.password_hash = user_doc['password']
        # NEW: Add role field with default fallback for existing users
        self.role = user_doc.get('role', 'user')
    
    # NEW: Helper method to check if user is admin
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    @staticmethod
    def get(user_id):
        """Get user by ID"""
        db = get_db()
        user_doc = db.users.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        db = get_db()
        user_doc = db.users.find_one({'username': username})
        if user_doc:
            return User(user_doc)
        return None
    
    @staticmethod
    def create_user(username, email, password, role='user'):
        """Create a new user with specified role (defaults to 'user')"""
        db = get_db()
        
        # Check if username already exists
        if db.users.find_one({'username': username}):
            return None  # Username already taken
        
        # Create new user document with role field
        user_doc = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'role': role  # NEW: Store role in database
        }
        
        # Insert into database
        result = db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        return User(user_doc)
    
    def check_password(self, password):
        """Check if provided password matches user's password"""
        return check_password_hash(self.password_hash, password)
