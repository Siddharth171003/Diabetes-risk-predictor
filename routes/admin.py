from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.db import get_db
from datetime import datetime
import uuid
from models.diabetes_model import DiabetesPredictor
from functools import wraps
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to ensure the user is an admin."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Enforce Flask-Login
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        # Also enforce JWT
        try:
            jwt_user_id = get_jwt_identity()
            # Optional: confirm JWT identity matches current_user.id
            if str(jwt_user_id) != current_user.id:
                flash('Invalid session.', 'error')
                return redirect(url_for('auth.login'))
        except Exception:
            flash('Authentication required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

def validate_name(name):
    return bool(re.fullmatch(r'[A-Za-z ]{3,}', name))
def validate_phone(phone):
    return bool(re.fullmatch(r'\d{10,15}', phone))
def validate_email(email):
    return bool(re.fullmatch(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email))

@admin_bp.route('/', methods=['GET'])
@jwt_required()
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    patients = list(db.patients.find().sort('created_at', -1))
    return render_template('admin_dashboard.html', patients=patients)

@admin_bp.route('/add', methods=['GET', 'POST'])
@jwt_required()
@login_required
@admin_required
def add_patient():
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        if not (name and phone and email):
            flash('Name, phone, and email are required.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
        if not validate_name(name):
            flash('Name must be at least 3 letters and contain only letters/spaces.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
        if not validate_phone(phone):
            flash('Phone must be 10 to 15 digits.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
        try:
            glucose         = float(request.form['glucose'])
            blood_pressure  = float(request.form['blood_pressure'])
            skin_thickness  = float(request.form['skin_thickness'])
            insulin         = float(request.form['insulin'])
            bmi             = float(request.form['bmi'])
            dpf             = float(request.form['diabetes_pedigree'])
            age             = float(request.form['age'])
            if age <= 0:
                flash('Age must be greater than 0.', 'error')
                return render_template('admin_add.html', name=name, phone=phone, email=email)
        except (ValueError, KeyError):
            flash('All health fields must be numeric and provided.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
        try:
            db = get_db()
            db.patients.insert_one({
                '_id': str(uuid.uuid4()),
                'name': name,
                'phone': phone,
                'email': email,
                'glucose': glucose,
                'blood_pressure': blood_pressure,
                'skin_thickness': skin_thickness,
                'insulin': insulin,
                'bmi': bmi,
                'diabetes_pedigree': dpf,
                'age': age,
                'created_at': datetime.utcnow()
            })
            flash('Patient added successfully.', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            current_app.logger.error(f"Error adding patient: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('admin_add.html', name=name, phone=phone, email=email)
    return render_template('admin_add.html')

@admin_bp.route('/predict/<patient_id>', methods=['GET'])
@jwt_required()
@login_required
@admin_required
def predict_patient(patient_id):
    db = get_db()
    patient = db.patients.find_one({'_id': patient_id})
    if not patient:
        flash('Patient not found.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    features = [
        patient['glucose'], patient['blood_pressure'],
        patient['skin_thickness'], patient['insulin'],
        patient['bmi'], patient['diabetes_pedigree'],
        patient['age']
    ]
    predictor = DiabetesPredictor()
    predictor.load_model()
    result = predictor.predict(features)
    return render_template('admin_predict.html', patient=patient, result=result)
