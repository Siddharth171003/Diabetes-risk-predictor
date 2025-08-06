from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, make_response, jsonify
)
from flask_login import login_user, logout_user, login_required
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
from models.user import User
from utils.db import get_db
import requests, re

auth_bp = Blueprint("auth", __name__)

# -----------------------
# Helper: Sanitization
# -----------------------
def sanitize(text: str) -> str:
    return text.strip() if text else ""

# -----------------------
# Helper: Validators
# -----------------------
def validate_username(username: str):
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 20:
        return False, "Username cannot exceed 20 characters."

    # First, ensure all characters are valid (letters, numbers, underscores, hyphens)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", username):
        return False, "Username may only contain letters, numbers, underscores, and hyphens."

    # Now, add the new condition: ensure at least one alphabet character is present
    if not re.search(r"[A-Za-z]", username):
        return False, "Username must contain at least one letter."

    return True, ""

def validate_email(email: str):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))

def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain a number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain a special character."
    return True, ""

# -----------------------
# Registration
# -----------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = sanitize(request.form.get("username"))
        email = sanitize(request.form.get("email"))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Presence checks
        if not username:
            flash("Username is required.", "error"); return render_template("register.html")
        if not email:
            flash("Email is required.", "error"); return render_template("register.html")
        if not password:
            flash("Password is required.", "error"); return render_template("register.html")
        if not confirm:
            flash("Password confirmation is required.", "error"); return render_template("register.html")

        # Username validation
        ok, msg = validate_username(username)
        if not ok:
            flash(msg, "error"); return render_template("register.html")

        # Email validation
        if not validate_email(email):
            flash("Please enter a valid email address.", "error"); return render_template("register.html")

        # Password validation
        ok, msg = validate_password(password)
        if not ok:
            flash(msg, "error"); return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error"); return render_template("register.html")

        # Uniqueness checks
        if User.get_by_username(username):
            flash("Username already exists. Choose another.", "error"); return render_template("register.html")
        db = get_db()
        if db.users.find_one({"email": email}):
            flash("Email already registered. Use a different email.", "error"); return render_template("register.html")

        # Create user
        user = User.create_user(username, email, password, role="user")
        if user:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        flash("Registration failed. Please try again.", "error")

    return render_template("register.html")


# -----------------------
# Login
# -----------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = sanitize(request.form.get("username"))
        password = request.form.get("password", "")
        token = request.form.get("g-recaptcha-response", "")

        # Presence checks
        if not username:
            flash("Username is required.", "error"); return render_template("login.html")
        if not password:
            flash("Password is required.", "error"); return render_template("login.html")

        # Basic username format
        if not (3 <= len(username) <= 20):
            flash("Invalid username format.", "error"); return render_template("login.html")

        # Credential check
        user = User.get_by_username(username)
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error"); return render_template("login.html")

        # reCAPTCHA
        if not token:
            flash("Please complete the reCAPTCHA.", "error"); return render_template("login.html")
        try:
            resp = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": current_app.config["RECAPTCHA_PRIVATE_KEY"],
                    "response": token
                },
                timeout=10
            )
            data = resp.json()
            if resp.status_code != 200 or not data.get("success"):
                flash("reCAPTCHA failed. Try again.", "error"); return render_template("login.html")
        except requests.RequestException:
            flash("reCAPTCHA verification error.", "error"); return render_template("login.html")

        # Log in & issue JWT
        login_user(user)
        access = create_access_token(identity=user.id)
        refresh = create_refresh_token(identity=user.id)
        response = make_response(redirect(url_for("dashboard")))
        set_access_cookies(response, access)
        set_refresh_cookies(response, refresh)
        flash("Login successful!", "success")
        return response

    return render_template("login.html")


# -----------------------
# Logout
# -----------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    response = make_response(redirect(url_for("auth.login")))
    unset_jwt_cookies(response)
    flash("You have been logged out.", "info")
    return response


# -----------------------
# Token Refresh
# -----------------------
@auth_bp.route("/token/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        new_access = create_access_token(identity=identity)
        resp = jsonify(access_token=new_access, success=True)
        set_access_cookies(resp, new_access)
        return resp, 200
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify(error="Token refresh failed"), 400


# -----------------------
# JWT-Protected Endpoints
# -----------------------
@auth_bp.route("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.get(user_id)
    if user:
        return jsonify({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin()
        }), 200
    return jsonify(error="User not found"), 404

@auth_bp.route("/jwt-status")
@jwt_required()
def jwt_status():
    try:
        uid = get_jwt_identity()
        return jsonify({
            "jwt_working": True,
            "user_id": uid,
            "message": "JWT is functioning properly."
        }), 200
    except Exception as e:
        return jsonify(jwt_working=False, error=str(e)), 401
