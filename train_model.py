"""
Train a simple ML model for exoplanet detection
This script creates a pre-trained model for the Stellar Scout application
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import requests

def fetch_training_data():
    """Fetch real exoplanet data from NASA for training"""
    print("📡 Fetching training data from NASA Exoplanet Archive...")
    
    NASA_API_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    
    params = {
        'query': '''select pl_name,st_teff,st_rad,st_mass,pl_orbper,pl_trandep,pl_rade 
                    from ps where default_flag=1 and pl_trandep is not null''',
        'format': 'json'
    }
    
    try:
        response = requests.get(NASA_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Fetched {len(data)} exoplanets with transit data")
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None


def create_synthetic_data(df):
    """Create synthetic non-exoplanet examples for training"""
    print("🔧 Creating synthetic training dataset...")
    
    # Positive examples (real exoplanets)
    positive_data = df[['st_teff', 'st_rad', 'st_mass', 'pl_orbper', 'pl_trandep']].copy()
    positive_data = positive_data.dropna()
    positive_data['has_exoplanet'] = 1
    
    # Create negative examples (stars without transiting planets)
    n_negative = len(positive_data)
    negative_data = pd.DataFrame({
        'st_teff': np.random.normal(5778, 1000, n_negative),  # Star temperature
        'st_rad': np.random.uniform(0.5, 2.0, n_negative),    # Star radius
        'st_mass': np.random.uniform(0.5, 2.0, n_negative),   # Star mass
        'pl_orbper': np.random.uniform(1, 1000, n_negative),  # Orbital period
        'pl_trandep': np.random.uniform(0, 0.001, n_negative), # Very shallow or no transit
        'has_exoplanet': 0
    })
    
    # Combine datasets
    training_data = pd.concat([positive_data, negative_data], ignore_index=True)
    
    print(f"✅ Created training set: {len(training_data)} samples")
    print(f"   - Positive examples (exoplanets): {len(positive_data)}")
    print(f"   - Negative examples (no exoplanet): {len(negative_data)}")
    
    return training_data


def train_model(training_data):
    """Train Random Forest model"""
    print("\n🤖 Training AI model...")
    
    # Prepare features and labels
    X = training_data[['st_teff', 'st_rad', 'st_mass', 'pl_orbper', 'pl_trandep']]
    y = training_data['has_exoplanet']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"✅ Model trained successfully!")
    print(f"   - Training accuracy: {train_score:.2%}")
    print(f"   - Testing accuracy: {test_score:.2%}")
    
    return model, scaler


def save_model(model, scaler):
    """Save trained model and scaler"""
    print("\n💾 Saving model...")
    
    # Save model
    with open('exoplanet_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Save scaler
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    print("✅ Model saved as 'exoplanet_model.pkl'")
    print("✅ Scaler saved as 'scaler.pkl'")


def test_model(model, scaler):
    """Test model with sample predictions"""
    print("\n🧪 Testing model with sample data...")
    
    # Test case 1: Earth-like planet around Sun-like star
    test_input_1 = np.array([[5778, 1.0, 1.0, 365.25, 0.01]])
    test_input_1_scaled = scaler.transform(test_input_1)
    prediction_1 = model.predict(test_input_1_scaled)[0]
    probability_1 = model.predict_proba(test_input_1_scaled)[0][1]
    
    print(f"\n Test 1: Earth-like planet")
    print(f"   Input: Temp=5778K, Radius=1.0, Mass=1.0, Period=365d, Depth=0.01%")
    print(f"   Prediction: {'Exoplanet' if prediction_1 == 1 else 'No Exoplanet'}")
    print(f"   Confidence: {probability_1:.2%}")
    
    # Test case 2: Hot Jupiter
    test_input_2 = np.array([[6000, 1.2, 1.1, 3.5, 0.02]])
    test_input_2_scaled = scaler.transform(test_input_2)
    prediction_2 = model.predict(test_input_2_scaled)[0]
    probability_2 = model.predict_proba(test_input_2_scaled)[0][1]
    
    print(f"\n Test 2: Hot Jupiter")
    print(f"   Input: Temp=6000K, Radius=1.2, Mass=1.1, Period=3.5d, Depth=0.02%")
    print(f"   Prediction: {'Exoplanet' if prediction_2 == 1 else 'No Exoplanet'}")
    print(f"   Confidence: {probability_2:.2%}")
    
    # Test case 3: No transit signal
    test_input_3 = np.array([[5500, 0.9, 0.95, 200, 0.0001]])
    test_input_3_scaled = scaler.transform(test_input_3)
    prediction_3 = model.predict(test_input_3_scaled)[0]
    probability_3 = model.predict_proba(test_input_3_scaled)[0][1]
    
    print(f"\n Test 3: Very shallow transit")
    print(f"   Input: Temp=5500K, Radius=0.9, Mass=0.95, Period=200d, Depth=0.0001%")
    print(f"   Prediction: {'Exoplanet' if prediction_3 == 1 else 'No Exoplanet'}")
    print(f"   Confidence: {probability_3:.2%}")


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("🌟 STELLAR SCOUT - ML MODEL TRAINING")
    print("=" * 60)
    
    # Fetch data
    df = fetch_training_data()
    
    if df is None or len(df) == 0:
        print("❌ Failed to fetch training data. Exiting.")
        return
    
    # Create training dataset
    training_data = create_synthetic_data(df)
    
    # Train model
    model, scaler = train_model(training_data)
    
    # Save model
    save_model(model, scaler)
    
    # Test model
    test_model(model, scaler)
    
    print("\n" + "=" * 60)
    print("✅ Training complete! Model ready for use.")
    print("=" * 60)


if __name__ == "__main__":
    main()