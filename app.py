from flask import Flask, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager, jwt_required
from config import Config
from utils.db import close_db
from models.user import User
from routes.auth import auth_bp
from routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Initialize Flask-JWT-Extended globally (for all blueprints and views)
    jwt = JWTManager(app)

    
    @jwt.unauthorized_loader
    def custom_unauth_loader(reason):
        flash("You must log in to access this page.", "error")
        return redirect(url_for("auth.login"))

    @jwt.invalid_token_loader
    def custom_invalid_loader(reason):
        flash("Session expired or invalid, please log in again.", "error")
        return redirect(url_for("auth.login"))

    @jwt.expired_token_loader
    def custom_expired_loader(header, payload):
        flash("Your session has expired. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    # Close database connection when app context ends
    app.teardown_appcontext(close_db)
    
    # Register authentication and admin blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Core routes

    @app.route('/')
    def index():
        try:
            # The JWT-protected UI expects session or JWT;
            # Since current_user is always defined, you can redirect based on that if you want,
            # or just always send to dashboard (which is itself protected)
            if current_user.is_authenticated:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Index error: {e}")
            return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    @jwt_required()
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/predict', methods=['GET', 'POST'])
    @jwt_required()
    def predict():
        # Always render the form by default
        if request.method == 'GET':
            return render_template('predict.html')
        # POST → handle submission
        try:
            user_data = [
                float(request.form['glucose']),
                float(request.form['blood_pressure']),
                float(request.form['skin_thickness']),
                float(request.form['insulin']),
                float(request.form['bmi']),
                float(request.form['diabetes_pedigree']),
                float(request.form['age'])
            ]

            # Run your ML predictor
            from models.diabetes_model import DiabetesPredictor
            predictor = DiabetesPredictor()
            predictor.load_model()
            result = predictor.predict(user_data)

            if not result:
                raise RuntimeError("Prediction returned no result")

            return render_template(
                'result.html',
                prediction=result['prediction'],
                risk_percentage=result['risk_percentage'],
                confidence=result['confidence'],
                user_data=user_data
            )
        except KeyError as e:
            flash(f"Missing form field: {e.args[0]}", 'error')
        except ValueError:
            flash("All health fields must be valid numbers.", 'error')
        except Exception as e:
            flash("Error making prediction. Please try again.", 'error')
            current_app.logger.error(f"Prediction error: {e}")

        return render_template('predict.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)