#!/usr/bin/env python3
from bson.objectid import ObjectId
from utils.db import get_db
from models.user import User
from app import create_app

def main():
    # Create and configure the Flask app
    app = create_app()

    # Push application context so get_db() can access `g`
    with app.app_context():
        db = get_db()

        # Change these to your desired admin credentials:
        admin_username = "Admin"
        admin_email    = "admin@gmail.com"
        admin_password = "Password@1234"

        # Check if the user already exists
        existing = db.users.find_one({ "username": admin_username })
        if existing:
            # Promote existing user to admin
            result = db.users.update_one(
                { "_id": existing["_id"] },
                { "$set": { "role": "admin" } }
            )
            if result.modified_count:
                print(f"✅ User '{admin_username}' promoted to admin.")
            else:
                print(f"ℹ️ User '{admin_username}' was already an admin.")
        else:
            # Create a brand-new admin user
            new_admin = User.create_user(
                admin_username,
                admin_email,
                admin_password,
                role="admin"
            )
            if new_admin:
                print(f"✅ New admin user '{admin_username}' created.")
            else:
                print(f"❌ Failed to create admin user '{admin_username}'. Perhaps the username is taken.")

if __name__ == "__main__":
    main()
