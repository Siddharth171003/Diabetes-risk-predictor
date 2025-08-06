import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix
)
from sklearn.preprocessing import StandardScaler
import pickle
import os
import xgboost as xgb


class DiabetesPredictor:
    def __init__(self):
        try:
            self.models = {
                'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
                'LogisticRegression': LogisticRegression(random_state=42, max_iter=1000),
                'KNN': KNeighborsClassifier(n_neighbors=5),
                'XGBoost': xgb.XGBClassifier(random_state=42, eval_metric='logloss')
            }
            self.best_model = None
            self.best_model_name = None
            self.scaler = StandardScaler()
            self.feature_names = [
                'Glucose', 'BloodPressure', 'SkinThickness',
                'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age',
                'Glucose_BMI', 'Age_DPF', 'High_Glucose',
                'BMI_Underweight', 'BMI_Healthy', 'BMI_Overweight', 'BMI_Obese'
            ]
            self.is_trained = False
            self.model_results = {}
        except Exception as e:
            raise Exception(f"Error in __init__: {e}")

    def load_data(self):
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'diabetes.csv')
            df = pd.read_csv(data_path)
            invalid_zero_cols = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
            for col in invalid_zero_cols:
                median_val = df.loc[df[col] > 0, col].median()
                df[col] = df[col].replace(0, median_val)
            df['Glucose_BMI'] = df['Glucose'] * df['BMI']
            df['Age_DPF'] = df['Age'] * df['DiabetesPedigreeFunction']
            df['High_Glucose'] = (df['Glucose'] > 140).astype(int)
            df['BMI_Underweight'] = (df['BMI'] < 18.5).astype(int)
            df['BMI_Healthy']     = ((df['BMI'] >= 18.5) & (df['BMI'] < 25)).astype(int)
            df['BMI_Overweight']  = ((df['BMI'] >= 25) & (df['BMI'] < 30)).astype(int)
            df['BMI_Obese']       = (df['BMI'] >= 30).astype(int)
            print("Dataset loaded, cleaned, and features engineered!")
            print(f"Shape: {df.shape}")
            return df
        except Exception as e:
            raise Exception(f"Error in load_data: {e}")

    def prepare_data(self, df):
        try:
            X = df.drop('Outcome', axis=1)
            y = df['Outcome']
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            print(f"Training samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")
            return X_train_scaled, X_test_scaled, y_train, y_test
        except Exception as e:
            raise Exception(f"Error in prepare_data: {e}")

    def evaluate_model(self, model, X_train, X_test, y_train, y_test, model_name):
        try:
            model.fit(X_train, y_train)
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            train_metrics = {
                'accuracy': accuracy_score(y_train, y_train_pred),
                'precision': precision_score(y_train, y_train_pred),
                'recall': recall_score(y_train, y_train_pred),
                'f1': f1_score(y_train, y_train_pred)
            }
            test_metrics = {
                'accuracy': accuracy_score(y_test, y_test_pred),
                'precision': precision_score(y_test, y_test_pred),
                'recall': recall_score(y_test, y_test_pred),
                'f1': f1_score(y_test, y_test_pred)
            }
            train_cm = confusion_matrix(y_train, y_train_pred)
            test_cm = confusion_matrix(y_test, y_test_pred)
            return {
                'model': model,
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'train_cm': train_cm,
                'test_cm': test_cm,
                'train_pred': y_train_pred,
                'test_pred': y_test_pred
            }
        except Exception as e:
            raise Exception(f"Error in evaluate_model ({model_name}): {e}")

    def train_model(self):
        try:
            print("Starting training and model comparison...")
            df = self.load_data()
            X_train, X_test, y_train, y_test = self.prepare_data(df)
            self.model_results = {}
            best_f1 = 0
            for model_name, model in self.models.items():
                print(f"\nTraining {model_name}...")
                results = self.evaluate_model(model, X_train, X_test, y_train, y_test, model_name)
                self.model_results[model_name] = results
                print(f"\n{model_name} Results:")
                print("-" * 50)
                print("TRAINING SET:")
                print(f"  Accuracy:  {results['train_metrics']['accuracy']:.4f}")
                print(f"  Precision: {results['train_metrics']['precision']:.4f}")
                print(f"  Recall:    {results['train_metrics']['recall']:.4f}")
                print(f"  F1 Score:  {results['train_metrics']['f1']:.4f}")
                print("\nTEST SET:")
                print(f"  Accuracy:  {results['test_metrics']['accuracy']:.4f}")
                print(f"  Precision: {results['test_metrics']['precision']:.4f}")
                print(f"  Recall:    {results['test_metrics']['recall']:.4f}")
                print(f"  F1 Score:  {results['test_metrics']['f1']:.4f}")
                print("\nConfusion Matrix (Test):")
                print(results['test_cm'])
                if results['test_metrics']['f1'] > best_f1:
                    best_f1 = results['test_metrics']['f1']
                    self.best_model = model
                    self.best_model_name = model_name
            summary_df = pd.DataFrame([
                {
                    'Model': name,
                    'Train_Accuracy': f"{res['train_metrics']['accuracy']:.4f}",
                    'Test_Accuracy': f"{res['test_metrics']['accuracy']:.4f}",
                    'Train_F1': f"{res['train_metrics']['f1']:.4f}",
                    'Test_F1': f"{res['test_metrics']['f1']:.4f}",
                    'Train_Precision': f"{res['train_metrics']['precision']:.4f}",
                    'Test_Precision': f"{res['test_metrics']['precision']:.4f}",
                    'Train_Recall': f"{res['train_metrics']['recall']:.4f}",
                    'Test_Recall': f"{res['test_metrics']['recall']:.4f}"
                } for name, res in self.model_results.items()
            ])
            print("\n" + "=" * 80)
            print("MODEL COMPARISON SUMMARY")
            print("=" * 80)
            print(summary_df.to_string(index=False))
            print(f"\n🏆 BEST MODEL: {self.best_model_name} (Test F1 Score: {best_f1:.4f})")
            self.model = self.best_model
            if hasattr(self.best_model, 'feature_importances_'):
                fi = pd.DataFrame({
                    'feature': self.feature_names,
                    'importance': self.best_model.feature_importances_
                }).sort_values('importance', ascending=False)
                print(f"\nFeature Importances ({self.best_model_name}):")
                print(fi)
            self.is_trained = True
            return True
        except Exception as e:
            raise Exception(f"Error in train_model: {e}")

    def save_model(self):
        try:
            if not self.is_trained:
                raise Exception("Model not trained yet!")
            model_data = {
                'model': self.best_model,
                'scaler': self.scaler,
                'model_name': self.best_model_name,
                'feature_names': self.feature_names
            }
            model_path = os.path.join(os.path.dirname(__file__), 'diabetes_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"Best model ({self.best_model_name}) and scaler saved to {model_path}")
            return True
        except Exception as e:
            raise Exception(f"Error in save_model: {e}")

    def load_model(self):
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'diabetes_model.pkl')
            with open(model_path, 'rb') as f:
                saved_data = pickle.load(f)
                self.best_model = saved_data['model']
                self.model = self.best_model
                self.scaler = saved_data['scaler']
                self.best_model_name = saved_data.get('model_name', 'Unknown')
                self.feature_names = saved_data.get('feature_names', self.feature_names)
            self.is_trained = True
            print(f"Model ({self.best_model_name}) and scaler loaded successfully!")
            return True
        except Exception as e:
            raise Exception(f"Error in load_model: {e}")

    def predict(self, input_data):
        try:
            if not self.is_trained:
                raise Exception("Model not trained yet!")
            base = list(input_data)
            engineered = [
                base[0] * base[4],
                base[6] * base[5],
                int(base[0] > 140),
                int(base[4] < 18.5),
                int(18.5 <= base[4] < 25),
                int(25 <= base[4] < 30),
                int(base[4] >= 30)
            ]
            full_features = base + engineered
            df = pd.DataFrame([full_features], columns=self.feature_names)
            df_scaled = self.scaler.transform(df)
            pred = self.best_model.predict(df_scaled)[0]
            probs = self.best_model.predict_proba(df_scaled)[0]
            return {
                'prediction': 'High Risk' if pred == 1 else 'Low Risk',
                'risk_percentage': round(probs[1] * 100, 2),
                'confidence': round(max(probs) * 100, 2),
                'model_used': self.best_model_name
            }
        except Exception as e:
            raise Exception(f"Error in predict: {e}")


if __name__ == "__main__":
    predictor = DiabetesPredictor()
    if predictor.train_model():
        predictor.save_model()
        print("\n" + "="*50)
        print("TESTING BEST MODEL")
        print("="*50)
        sample_data = [140, 78, 35, 100, 25, 0.65, 50]
        result = predictor.predict(sample_data)
        if result:
            print("Result:", result)
