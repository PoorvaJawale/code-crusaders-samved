"""
Predictive Layer for Traffic Forecasting
Uses historical MongoDB data to predict future traffic patterns.
"""
import numpy as np
from sklearn.linear_model import LinearRegression
from db import get_density_history
from datetime import datetime, timedelta


def predict_traffic_trend(minutes_ahead=15):
    """
    Predict traffic density for the next N minutes using simple linear regression.
    
    Args:
        minutes_ahead: How many minutes ahead to predict
        
    Returns:
        int: Predicted vehicle count per minute
    """
    try:
        # Get historical data
        history = get_density_history(limit=100)
        
        if not history or len(history) < 5:
            # Not enough data, return average or default
            return 25
        
        # Extract vehicle counts and timestamps
        counts = [record.get('vehicle_count', 0) for record in history]
        
        # Simple moving average if we have limited data
        if len(counts) < 10:
            return int(np.mean(counts))
        
        # Prepare data for linear regression
        X = np.arange(len(counts)).reshape(-1, 1)  # Time index
        y = np.array(counts)
        
        # Train simple linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict for next time step
        next_step = len(counts) + (minutes_ahead / 5)  # Assuming data every 5 mins
        prediction = model.predict([[next_step]])[0]
        
        # Ensure prediction is reasonable (non-negative, not too extreme)
        prediction = max(0, min(prediction, 200))
        
        return int(prediction)
        
    except Exception as e:
        print(f"[PREDICTION ERROR] {e}")
        return 25  # Default fallback


def analyze_peak_hours(location="default"):
    """
    Analyze historical data to identify peak traffic hours.
    
    Returns:
        dict: Peak hours analysis with time periods and congestion levels
    """
    try:
        history = get_density_history(limit=500)
        
        if not history:
            return {
                "peak_morning": "8:00-10:00 AM",
                "peak_evening": "5:00-7:00 PM",
                "avg_density": 0
            }
        
        # Group by hour and calculate average density
        hourly_data = {}
        for record in history:
            timestamp = record.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            hour = timestamp.hour
            count = record.get('vehicle_count', 0)
            
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(count)
        
        # Calculate averages
        hourly_avg = {h: np.mean(counts) for h, counts in hourly_data.items()}
        
        # Find peak hours
        if hourly_avg:
            sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
            peak_hour = sorted_hours[0][0] if sorted_hours else 9
            
            return {
                "peak_morning": f"{peak_hour}:00",
                "peak_evening": "5:00-7:00 PM",
                "avg_density": int(np.mean(list(hourly_avg.values()))),
                "hourly_data": hourly_avg
            }
        
        return {"peak_morning": "9:00 AM", "peak_evening": "6:00 PM", "avg_density": 0}
        
    except Exception as e:
        print(f"[ANALYSIS ERROR] {e}")
        return {"peak_morning": "9:00 AM", "peak_evening": "6:00 PM", "avg_density": 0}


def detect_congestion_trend():
    """
    Detect if congestion is increasing, decreasing, or stable.
    
    Returns:
        str: "increasing", "decreasing", or "stable"
    """
    try:
        recent_data = get_density_history(limit=10)
        
        if len(recent_data) < 5:
            return "stable"
        
        counts = [record.get('vehicle_count', 0) for record in recent_data]
        
        # Compare first half vs second half
        mid = len(counts) // 2
        first_half_avg = np.mean(counts[:mid])
        second_half_avg = np.mean(counts[mid:])
        
        diff_threshold = 5
        
        if second_half_avg - first_half_avg > diff_threshold:
            return "increasing"
        elif first_half_avg - second_half_avg > diff_threshold:
            return "decreasing"
        else:
            return "stable"
            
    except Exception as e:
        print(f"[TREND ERROR] {e}")
        return "stable"
