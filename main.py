from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import numpy as np
import pickle
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Stellar Scout API", version="1.0.0")

# CORS Configuration - Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NASA Exoplanet Archive API Configuration
NASA_API_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NASA_QUERY_BASE = "query=select+*+from+ps+where+default_flag=1"

# Global cache for exoplanet data
exoplanet_cache = []
cache_timestamp = None
CACHE_DURATION = 3600  # 1 hour in seconds

# Load pre-trained ML model (you'll need to train and save this)
try:
    with open('exoplanet_model.pkl', 'rb') as f:
        ml_model = pickle.load(f)
    print("✅ ML Model loaded successfully")
except:
    ml_model = None
    print("⚠️ ML Model not found. Using fallback prediction method.")


# Pydantic Models for Request/Response
class PredictionRequest(BaseModel):
    star_temp: float
    star_radius: float
    star_mass: float
    orbital_period: float
    transit_depth: float


class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    planet_type: str
    habitable_zone: str


class ExoplanetResponse(BaseModel):
    name: str
    hostname: Optional[str]
    discoverymethod: Optional[str]
    disc_year: Optional[int]
    pl_rade: Optional[float]
    pl_bmasse: Optional[float]
    pl_orbper: Optional[float]
    sy_dist: Optional[float]
    st_teff: Optional[float]
    st_rad: Optional[float]


# Helper Functions
def fetch_nasa_data():
    """Fetch exoplanet data from NASA API"""
    global exoplanet_cache, cache_timestamp
    
    # Check cache validity
    if exoplanet_cache and cache_timestamp:
        elapsed = (datetime.now() - cache_timestamp).total_seconds()
        if elapsed < CACHE_DURATION:
            return exoplanet_cache
    
    try:
        # NASA TAP API query
        params = {
            'query': 'select pl_name,hostname,discoverymethod,disc_year,pl_rade,pl_bmasse,pl_orbper,sy_dist,st_teff,st_rad from ps where default_flag=1',
            'format': 'json'
        }
        
        response = requests.get(NASA_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        exoplanet_cache = data
        cache_timestamp = datetime.now()
        
        print(f"✅ Fetched {len(exoplanet_cache)} exoplanets from NASA")
        return exoplanet_cache
        
    except Exception as e:
        print(f"❌ Error fetching NASA data: {e}")
        # Return cached data if available
        if exoplanet_cache:
            return exoplanet_cache
        # Return empty list as fallback
        return []


def calculate_planet_type(radius):
    """Determine planet type based on radius"""
    if radius is None:
        return "Unknown"
    
    if radius < 1.25:
        return "Earth-like"
    elif radius < 2.0:
        return "Super-Earth"
    elif radius < 6.0:
        return "Neptune-like"
    else:
        return "Jupiter-like"


def calculate_habitable_zone(star_temp, orbital_period, star_radius):
    """Estimate if planet is in habitable zone"""
    try:
        # Simplified habitable zone calculation
        # Based on stellar temperature and orbital distance
        
        # Calculate semi-major axis (AU) from orbital period
        # Kepler's third law: a^3 = P^2 * M (assuming M=1 solar mass)
        orbital_period_years = orbital_period / 365.25
        semi_major_axis = orbital_period_years ** (2/3)
        
        # Habitable zone boundaries (rough estimate)
        # Inner: 0.95 * sqrt(L/L_sun), Outer: 1.37 * sqrt(L/L_sun)
        # L/L_sun ≈ (T/T_sun)^4 * (R/R_sun)^2
        
        temp_ratio = star_temp / 5778  # Sun temperature
        radius_ratio = star_radius if star_radius else 1.0
        luminosity_ratio = (temp_ratio ** 4) * (radius_ratio ** 2)
        
        inner_hz = 0.95 * np.sqrt(luminosity_ratio)
        outer_hz = 1.37 * np.sqrt(luminosity_ratio)
        
        if inner_hz <= semi_major_axis <= outer_hz:
            return "Habitable Zone"
        elif semi_major_axis < inner_hz:
            return "Too Hot"
        else:
            return "Too Cold"
    except:
        return "Unknown"


# API Endpoints

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Stellar Scout API",
        "version": "1.0.0",
        "endpoints": {
            "stats": "/api/stats",
            "exoplanets": "/api/exoplanets",
            "predict": "/api/predict",
            "chart-data": "/api/chart-data"
        }
    }


@app.get("/api/stats")
def get_stats():
    """Get statistics about exoplanets"""
    try:
        data = fetch_nasa_data()
        
        total_exoplanets = len(data)
        
        # Count potentially habitable (Earth-like size)
        habitable_count = sum(
            1 for planet in data 
            if planet.get('pl_rade') and 0.5 <= planet['pl_rade'] <= 1.5
        )
        
        # Count recent discoveries (2024)
        recent_count = sum(
            1 for planet in data 
            if planet.get('disc_year') and planet['disc_year'] >= 2024
        )
        
        return {
            "total_exoplanets": total_exoplanets,
            "habitable_exoplanets": habitable_count,
            "recent_discoveries": recent_count
        }
    except Exception as e:
        print(f"Error in get_stats: {e}")
        # Return default values
        return {
            "total_exoplanets": 5000,
            "habitable_exoplanets": 60,
            "recent_discoveries": 150
        }


@app.get("/api/exoplanets")
def get_exoplanets(page: int = 1, limit: int = 12):
    """Get paginated list of exoplanets"""
    try:
        data = fetch_nasa_data()
        
        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_data = data[start_idx:end_idx]
        has_more = end_idx < len(data)
        
        # Format response
        exoplanets = []
        for planet in paginated_data:
            exoplanets.append({
                "name": planet.get('pl_name', 'Unknown'),
                "hostname": planet.get('hostname'),
                "discoverymethod": planet.get('discoverymethod'),
                "disc_year": planet.get('disc_year'),
                "pl_rade": planet.get('pl_rade'),
                "pl_bmasse": planet.get('pl_bmasse'),
                "pl_orbper": planet.get('pl_orbper'),
                "sy_dist": planet.get('sy_dist'),
                "st_teff": planet.get('st_teff'),
                "st_rad": planet.get('st_rad')
            })
        
        return {
            "exoplanets": exoplanets,
            "page": page,
            "limit": limit,
            "total": len(data),
            "has_more": has_more
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exoplanets: {str(e)}")


@app.post("/api/predict", response_model=PredictionResponse)
def predict_exoplanet(request: PredictionRequest):
    """Predict exoplanet presence using AI model"""
    try:
        # Prepare features
        features = np.array([[
            request.star_temp,
            request.star_radius,
            request.star_mass,
            request.orbital_period,
            request.transit_depth
        ]])
        
        # Make prediction
        if ml_model is not None:
            prediction = ml_model.predict(features)[0]
            probability = ml_model.predict_proba(features)[0][1]
        else:
            # Fallback: Rule-based prediction
            # Transit depth suggests planet size
            # Larger transit depth = larger planet = more likely detection
            transit_score = min(request.transit_depth * 100, 1.0)
            
            # Stars similar to Sun are more likely to have detectable planets
            temp_score = 1.0 - abs(request.star_temp - 5778) / 5778
            temp_score = max(0, min(temp_score, 1.0))
            
            # Combine scores
            probability = (transit_score * 0.7 + temp_score * 0.3)
            prediction = 1 if probability > 0.5 else 0
        
        # Estimate planet radius from transit depth
        estimated_radius = np.sqrt(request.transit_depth / 100) * request.star_radius
        planet_type = calculate_planet_type(estimated_radius)
        
        # Calculate habitable zone
        habitable_zone = calculate_habitable_zone(
            request.star_temp,
            request.orbital_period,
            request.star_radius
        )
        
        return PredictionResponse(
            prediction=int(prediction),
            probability=float(probability),
            planet_type=planet_type,
            habitable_zone=habitable_zone
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.get("/api/chart-data")
def get_chart_data():
    """Get data for visualization charts"""
    try:
        data = fetch_nasa_data()
        
        # Timeline data (discoveries by year)
        timeline = {}
        for planet in data:
            year = planet.get('disc_year')
            if year and year >= 1990:  # Only recent discoveries
                timeline[year] = timeline.get(year, 0) + 1
        
        timeline_sorted = dict(sorted(timeline.items()))
        
        # Discovery methods distribution
        methods = {}
        for planet in data:
            method = planet.get('discoverymethod', 'Unknown')
            methods[method] = methods.get(method, 0) + 1
        
        # Planet size distribution
        sizes = {"Earth-like": 0, "Super-Earth": 0, "Neptune-like": 0, "Jupiter-like": 0, "Unknown": 0}
        for planet in data:
            radius = planet.get('pl_rade')
            planet_type = calculate_planet_type(radius)
            sizes[planet_type] += 1
        
        # Distance distribution
        distances = {"<50 ly": 0, "50-100 ly": 0, "100-500 ly": 0, ">500 ly": 0, "Unknown": 0}
        for planet in data:
            dist = planet.get('sy_dist')
            if dist is None:
                distances["Unknown"] += 1
            elif dist < 50:
                distances["<50 ly"] += 1
            elif dist < 100:
                distances["50-100 ly"] += 1
            elif dist < 500:
                distances["100-500 ly"] += 1
            else:
                distances[">500 ly"] += 1
        
        return {
            "timeline": timeline_sorted,
            "methods": methods,
            "sizes": sizes,
            "distances": distances
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart data: {str(e)}")


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ml_model_loaded": ml_model is not None,
        "cache_active": len(exoplanet_cache) > 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)