#!/usr/bin/env python3
"""
Test script to debug registration issues
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_service import UserService
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def test_registration():
    """Test the registration process"""
    try:
        # Initialize UserService
        db_path = "database/coffee_shop.db"
        user_service = UserService(db_path)
        
        print("Testing UserService...")
        
        # Test data with unique email
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test{unique_id}@example.com"
        test_name = "Test User"
        test_password = "password123"
        
        # Check if user already exists
        existing_user = user_service.get_user_by_email(test_email)
        if existing_user:
            print(f"User {test_email} already exists")
            return
        
        # Create user data
        user_data = {
            "name": test_name,
            "email": test_email,
            "password_hash": hash_password(test_password),
            "is_active": True
        }
        
        print("Creating user...")
        print(f"User data: {user_data}")
        
        # Create user
        user = user_service.create_user(user_data)
        
        print(f"User created successfully: {user}")
        
        # Verify user was created
        created_user = user_service.get_user_by_email(test_email)
        if created_user:
            print(f"User verified: {created_user}")
        else:
            print("ERROR: User not found after creation")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration() 