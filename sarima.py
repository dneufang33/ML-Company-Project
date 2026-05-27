import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
warnings.filterwarnings('ignore')

# Read the data
try:
    # Assuming the file is uploaded and accessible
    df = pd.read_excel('df.xlsx')  # Replace with actual filename
    print("Data loaded successfully!")
    print(f"Data shape: {df.shape}")
    print("\nFirst few rows:")
    print(df.head())
    
except FileNotFoundError:
    # Create sample data based on the provided structure for demonstration
    print("Creating sample data for demonstration...")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    
    sample_data = []
    coating_ids = list(range(1, 21))  # 20 coating IDs
    
    for date in dates:
        # Randomly select 5-15 coating IDs per day
        selected_coatings = np.random.choice(coating_ids, size=np.random.randint(5, 16), replace=False)
        
        for coating_id in selected_coatings:
            # Generate realistic fill rate data with some trend and seasonality
            base_fill_rate = 0.5 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365.25)
            noise = np.random.normal(0, 0.1)
            coating_effect = (coating_id - 10) * 0.01  # Different coating IDs have different base rates
            
            fill_rate = np.clip(base_fill_rate + coating_effect + noise, 0.1, 0.95)
            
            sample_data.append({
                'order_date': date,
                'coating_id': coating_id,
                'target_fill_rate': fill_rate,
                'CHF': np.random.uniform(100, 5000),
                'Customer_id': np.random.randint(1, 100),
                'num_orders': np.random.randint(1, 20)
            })
    
    df = pd.DataFrame(sample_data)
    print(f"Sample data created with shape: {df.shape}")

# Convert order_date to datetime
df['order_date'] = pd.to_datetime(df['order_date'])

# Identify top 10 coating IDs by frequency
top_coating_ids = df['coating_id'].value_counts().head(10).index.tolist()
print(f"\nTop 10 coating IDs by frequency: {top_coating_ids}")

# Filter data for top 10 coating IDs
df_filtered = df[df['coating_id'].isin(top_coating_ids)].copy()
print(f"Filtered data shape: {df_filtered.shape}")

# Function to check stationarity
def check_stationarity(ts, title):
    """
    Check if time series is stationary using Augmented Dickey-Fuller test
    """
    print(f"\n=== Stationarity Test for {title} ===")
    
    # Perform ADF test
    result = adfuller(ts.dropna())
    
    print(f'ADF Statistic: {result[0]:.6f}')
    print(f'p-value: {result[1]:.6f}')
    print('Critical Values:')
    for key, value in result[4].items():
        print(f'\t{key}: {value:.3f}')
    
    if result[1] <= 0.05:
        print("✓ Series is stationary (reject null hypothesis)")
        return True
    else:
        print("✗ Series is non-stationary (fail to reject null hypothesis)")
        return False

# Function to make series stationary
def make_stationary(ts, max_diff=2):
    """
    Make time series stationary by differencing
    """
    original_ts = ts.copy()
    diff_order = 0
    
    for i in range(max_diff + 1):
        if i == 0:
            current_ts = ts
        else:
            current_ts = ts.diff().dropna()
            
        is_stationary = check_stationarity(current_ts, f"Differenced {i} times")
        
        if is_stationary:
            diff_order = i
            break
        
        if i < max_diff:
            ts = current_ts
    
    return ts if diff_order > 0 else original_ts, diff_order

# Function to find optimal SARIMA parameters
def find_optimal_sarima(ts, max_p=3, max_d=2, max_q=3, max_P=2, max_D=1, max_Q=2, s=7):
    """
    Find optimal SARIMA parameters using AIC
    """
    best_aic = float('inf')
    best_params = None
    best_seasonal = None
    
    print("\nSearching for optimal SARIMA parameters...")
    
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                for P in range(max_P + 1):
                    for D in range(max_D + 1):
                        for Q in range(max_Q + 1):
                            try:
                                model = SARIMAX(ts, 
                                              order=(p, d, q),
                                              seasonal_order=(P, D, Q, s),
                                              enforce_stationarity=False,
                                              enforce_invertibility=False)
                                
                                fitted_model = model.fit(disp=False)
                                
                                if fitted_model.aic < best_aic:
                                    best_aic = fitted_model.aic
                                    best_params = (p, d, q)
                                    best_seasonal = (P, D, Q, s)
                                    
                            except:
                                continue
    
    print(f"Best SARIMA parameters: {best_params}")
    print(f"Best seasonal parameters: {best_seasonal}")
    print(f"Best AIC: {best_aic:.2f}")
    
    return best_params, best_seasonal

# Function to build and evaluate SARIMA model
def build_sarima_model(ts, order, seasonal_order):
    """
    Build and evaluate SARIMA model
    """
    try:
        model = SARIMAX(ts, 
                       order=order,
                       seasonal_order=seasonal_order,
                       enforce_stationarity=False,
                       enforce_invertibility=False)
        
        fitted_model = model.fit(disp=False)
        
        return fitted_model
    
    except Exception as e:
        print(f"Error building model: {e}")
        return None

# Function to forecast fill rate impact
def forecast_fill_rate_impact(model, coating_id, steps=30):
    """
    Forecast fill rate for a specific coating ID
    """
    try:
        forecast = model.forecast(steps=steps)
        conf_int = model.get_forecast(steps=steps).conf_int()
        
        return forecast, conf_int
    
    except Exception as e:
        print(f"Error forecasting: {e}")
        return None, None

# Main analysis
print("\n" + "="*50)
print("SARIMA MODEL ANALYSIS FOR FILL RATE PREDICTION")
print("="*50)

# Create individual models for each coating ID
coating_models = {}
coating_forecasts = {}

for coating_id in top_coating_ids:
    print(f"\n{'='*30}")
    print(f"ANALYZING COATING ID: {coating_id}")
    print(f"{'='*30}")
    
    # Filter data for this coating ID
    coating_data = df_filtered[df_filtered['coating_id'] == coating_id].copy()
    
    if len(coating_data) < 30:  # Need minimum data points
        print(f"Insufficient data for coating ID {coating_id} (only {len(coating_data)} points)")
        continue
    
    # Create daily time series
    daily_ts = coating_data.groupby('order_date')['target_fill_rate'].mean()
    daily_ts = daily_ts.reindex(pd.date_range(daily_ts.index.min(), daily_ts.index.max(), freq='D'))
    daily_ts = daily_ts.interpolate(method='linear')  # Fill missing dates
    
    print(f"Time series length: {len(daily_ts)}")
    print(f"Date range: {daily_ts.index.min()} to {daily_ts.index.max()}")
    
    # Check and make stationary if needed
    stationary_ts, diff_order = make_stationary(daily_ts)
    
    if len(stationary_ts) < 20:
        print(f"Time series too short after differencing for coating ID {coating_id}")
        continue
    
    # Find optimal parameters (simplified search for demonstration)
    try:
        # Use a simplified parameter search for faster execution
        best_params = (1, diff_order, 1)
        best_seasonal = (1, 1, 1, 7)  # Weekly seasonality
        
        print(f"Using SARIMA parameters: {best_params}")
        print(f"Using seasonal parameters: {best_seasonal}")
        
        # Build model
        model = build_sarima_model(daily_ts, best_params, best_seasonal)
        
        if model is not None:
            coating_models[coating_id] = model
            
            # Generate forecast
            forecast, conf_int = forecast_fill_rate_impact(model, coating_id, steps=30)
            
            if forecast is not None:
                coating_forecasts[coating_id] = {
                    'forecast': forecast,
                    'conf_int': conf_int,
                    'model_summary': model.summary()
                }
                
                print(f"✓ Model successfully built for coating ID {coating_id}")
                print(f"Model AIC: {model.aic:.2f}")
                
                # Print next 7 days forecast
                print(f"\nNext 7 days forecast:")
                for i in range(min(7, len(forecast))):
                    print(f"Day {i+1}: {forecast.iloc[i]:.4f}")
            
        else:
            print(f"✗ Failed to build model for coating ID {coating_id}")
            
    except Exception as e:
        print(f"✗ Error processing coating ID {coating_id}: {e}")

print(f"\n{'='*50}")
print("SUMMARY")
print(f"{'='*50}")
print(f"Successfully built models for {len(coating_models)} coating IDs")
print(f"Coating IDs with models: {list(coating_models.keys())}")

# Function to predict fill rate impact of a new order
def predict_order_impact(coating_id, order_date=None):
    """
    Predict how a new order will contribute to fill rate
    """
    if coating_id not in coating_models:
        return f"No model available for coating ID {coating_id}"
    
    model = coating_models[coating_id]
    
    if coating_id in coating_forecasts:
        forecast = coating_forecasts[coating_id]['forecast']
        
        # Get prediction for the specific date or next available
        if order_date is None:
            predicted_fill_rate = forecast.iloc[0]
            prediction_date = forecast.index[0]
        else:
            # Find closest forecast date
            order_date = pd.to_datetime(order_date)
            closest_idx = 0  # Simplified - use first forecast
            predicted_fill_rate = forecast.iloc[closest_idx]
            prediction_date = forecast.index[closest_idx]
        
        return {
            'coating_id': coating_id,
            'predicted_fill_rate': predicted_fill_rate,
            'prediction_date': prediction_date,
            'interpretation': f"An order for coating ID {coating_id} is predicted to have a fill rate of {predicted_fill_rate:.4f}"
        }
    
    return f"No forecast available for coating ID {coating_id}"

# Example predictions
print(f"\n{'='*50}")
print("EXAMPLE PREDICTIONS")
print(f"{'='*50}")

for coating_id in list(coating_models.keys())[:3]:  # Show first 3
    prediction = predict_order_impact(coating_id)
    if isinstance(prediction, dict):
        print(f"\nCoating ID {coating_id}:")
        print(f"  Predicted Fill Rate: {prediction['predicted_fill_rate']:.4f}")
        print(f"  Interpretation: {prediction['interpretation']}")

print(f"\n{'='*50}")
print("MODEL USAGE INSTRUCTIONS")
print(f"{'='*50}")
print("""
To predict fill rate for a new order:

1. Use predict_order_impact(coating_id) function
2. The function returns predicted fill rate based on SARIMA model
3. Models are available for coating IDs: """ + str(list(coating_models.keys())) + """

Example usage:
prediction = predict_order_impact(1)  # For coating ID 1
print(prediction)
""")

# Visualization function
def plot_forecast(coating_id, n_days=30):
    """
    Plot historical data and forecast for a coating ID
    """
    if coating_id not in coating_forecasts:
        print(f"No forecast available for coating ID {coating_id}")
        return
    
    # Get historical data
    coating_data = df_filtered[df_filtered['coating_id'] == coating_id].copy()
    daily_ts = coating_data.groupby('order_date')['target_fill_rate'].mean()
    
    # Get forecast
    forecast = coating_forecasts[coating_id]['forecast']
    conf_int = coating_forecasts[coating_id]['conf_int']
    
    plt.figure(figsize=(12, 6))
    
    # Plot historical data
    plt.plot(daily_ts.index, daily_ts.values, label='Historical Fill Rate', color='blue')
    
    # Plot forecast
    forecast_dates = pd.date_range(start=daily_ts.index.max() + pd.Timedelta(days=1), 
                                  periods=len(forecast), freq='D')
    plt.plot(forecast_dates, forecast.values, label='Forecast', color='red', linestyle='--')
    
    # Plot confidence intervals
    plt.fill_between(forecast_dates, 
                    conf_int.iloc[:, 0], 
                    conf_int.iloc[:, 1], 
                    color='red', alpha=0.2, label='Confidence Interval')
    
    plt.title(f'Fill Rate Forecast for Coating ID {coating_id}')
    plt.xlabel('Date')
    plt.ylabel('Fill Rate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

print("\nTo visualize forecasts, use: plot_forecast(coating_id)")

# CRITICAL ISSUES ANALYSIS AND MODEL VALIDATION
print(f"\n{'='*60}")
print("CRITICAL ISSUES ANALYSIS")
print(f"{'='*60}")

print("""
IDENTIFIED PROBLEMS WITH ORIGINAL MODEL:

1. NO VALIDATION:
   - Models trained on full dataset without train/test split
   - No out-of-sample testing performed
   - No prediction error metrics calculated

2. NEGATIVE VALUES IN SOME PREDICTIONS:
   - Some predictions are negative (e.g., -0.78, -2.12)
   - While fill rates can exceed 1.0 (over-filling), they cannot be negative

3. HIGH AIC VALUES:
   - High AIC values suggest potential overfitting
   - Need to validate actual predictive performance

4. NO BASELINE COMPARISON:
   - Missing comparison to simple forecasting methods
   - Cannot assess if SARIMA adds value over naive approaches

NOTE: Fill rates > 1.0 are realistic and can occur when:
- Orders are over-filled due to production constraints
- Batch production exceeds individual order requirements
- Multiple small orders filled from single production run
""")

# IMPROVED MODEL WITH VALIDATION
print(f"\n{'='*60}")
print("BUILDING IMPROVED MODEL WITH VALIDATION")
print(f"{'='*60}")

from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

def validate_and_improve_model(coating_id, test_size=30):
    """
    Build and validate SARIMA model with proper train/test split
    Calculate MAE for 1-day ahead predictions
    """
    print(f"\n--- Validating Model for Coating ID {coating_id} ---")
    
    # Get data for this coating ID
    coating_data = df_filtered[df_filtered['coating_id'] == coating_id].copy()
    
    if len(coating_data) < 50:
        print(f"Insufficient data for coating ID {coating_id}")
        return None
    
    # Create daily time series
    daily_ts = coating_data.groupby('order_date')['target_fill_rate'].mean()
    daily_ts = daily_ts.reindex(pd.date_range(daily_ts.index.min(), daily_ts.index.max(), freq='D'))
    daily_ts = daily_ts.interpolate(method='linear')
    
    # Check data characteristics
    print(f"Data range: {daily_ts.min():.4f} to {daily_ts.max():.4f}")
    print(f"Data mean: {daily_ts.mean():.4f}")
    print(f"Data std: {daily_ts.std():.4f}")
    
    # Fill rates can exceed 1.0 when orders are over-filled
    if daily_ts.max() > 5:
        print("INFO: High fill rate values detected (>5). This could indicate:")
        print("- Multiple orders filled from single production run")
        print("- Over-production scenarios")
        print("- Data aggregation effects")
    
    # Split into train/test
    train_size = len(daily_ts) - test_size
    train_data = daily_ts.iloc[:train_size]
    test_data = daily_ts.iloc[train_size:]
    
    print(f"Training period: {train_data.index[0]} to {train_data.index[-1]}")
    print(f"Testing period: {test_data.index[0]} to {test_data.index[-1]}")
    print(f"Train size: {len(train_data)}, Test size: {len(test_data)}")
    
    # Build model on training data only
    try:
        # Check stationarity of training data
        adf_result = adfuller(train_data.dropna())
        is_stationary = adf_result[1] <= 0.05
        
        if is_stationary:
            order = (1, 0, 1)
        else:
            # Try with differencing
            diff_data = train_data.diff().dropna()
            adf_result_diff = adfuller(diff_data)
            if adf_result_diff[1] <= 0.05:
                order = (1, 1, 1)
            else:
                order = (1, 2, 1)
        
        # Fit model
        model = SARIMAX(train_data, 
                       order=order,
                       seasonal_order=(1, 1, 1, 7),
                       enforce_stationarity=False,
                       enforce_invertibility=False)
        
        fitted_model = model.fit(disp=False)
        
        # One-step ahead predictions for test period
        predictions = []
        actuals = []
        
        # Rolling forecast approach for 1-day ahead predictions
        current_train = train_data.copy()
        
        for i in range(len(test_data)):
            # Fit model on current training data
            temp_model = SARIMAX(current_train, 
                               order=order,
                               seasonal_order=(1, 1, 1, 7),
                               enforce_stationarity=False,
                               enforce_invertibility=False)
            
            temp_fitted = temp_model.fit(disp=False)
            
            # Make 1-day ahead prediction
            forecast = temp_fitted.forecast(steps=1)
            predictions.append(forecast.iloc[0])
            actuals.append(test_data.iloc[i])
            
            # Add actual observation to training data for next iteration
            current_train = pd.concat([current_train, test_data.iloc[i:i+1]])
        
        # Calculate metrics
        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mape = np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100
        
        # Calculate baseline MAE (naive forecast - use last known value)
        naive_predictions = [train_data.iloc[-1]] * len(test_data)
        naive_mae = mean_absolute_error(actuals, naive_predictions)
        
        results = {
            'coating_id': coating_id,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'naive_mae': naive_mae,
            'improvement': (naive_mae - mae) / naive_mae * 100,
            'predictions': predictions,
            'actuals': actuals,
            'model': fitted_model,
            'data_range': (daily_ts.min(), daily_ts.max()),
            'train_size': len(train_data),
            'test_size': len(test_data)
        }
        
        print(f"✓ Model validation completed")
        print(f"MAE (1-day ahead): {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        print(f"MAPE: {mape:.2f}%")
        print(f"Naive MAE: {naive_mae:.4f}")
        print(f"Improvement over naive: {results['improvement']:.2f}%")
        
        if results['improvement'] < 0:
            print("⚠️  WARNING: Model performs worse than naive forecast!")
        
        return results
        
    except Exception as e:
        print(f"✗ Error in model validation: {e}")
        return None

# Validate models for all coating IDs
print(f"\n{'='*60}")
print("COMPREHENSIVE MODEL VALIDATION")
print(f"{'='*60}")

validation_results = {}
summary_metrics = []

for coating_id in top_coating_ids:
    results = validate_and_improve_model(coating_id, test_size=30)
    if results:
        validation_results[coating_id] = results
        summary_metrics.append({
            'coating_id': coating_id,
            'mae': results['mae'],
            'rmse': results['rmse'],
            'mape': results['mape'],
            'improvement': results['improvement'],
            'data_range_min': results['data_range'][0],
            'data_range_max': results['data_range'][1]
        })

# Summary table
if summary_metrics:
    summary_df = pd.DataFrame(summary_metrics)
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY - 1-DAY AHEAD PREDICTIONS")
    print(f"{'='*60}")
    print(summary_df.to_string(index=False, float_format='%.4f'))
    
    print(f"\nOVERALL STATISTICS:")
    print(f"Average MAE: {summary_df['mae'].mean():.4f}")
    print(f"Average RMSE: {summary_df['rmse'].mean():.4f}")
    print(f"Average MAPE: {summary_df['mape'].mean():.2f}%")
    print(f"Models with positive improvement: {(summary_df['improvement'] > 0).sum()}/{len(summary_df)}")

# Function to plot validation results
def plot_validation_results(coating_id, n_points=30):
    """
    Plot actual vs predicted values for validation period
    """
    if coating_id not in validation_results:
        print(f"No validation results for coating ID {coating_id}")
        return
    
    results = validation_results[coating_id]
    
    plt.figure(figsize=(12, 8))
    
    # Create subplot layout
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Actual vs Predicted
    ax1.plot(range(len(results['actuals'])), results['actuals'], 
             label='Actual', marker='o', color='blue')
    ax1.plot(range(len(results['predictions'])), results['predictions'], 
             label='Predicted', marker='s', color='red')
    ax1.set_title(f'Coating ID {coating_id}: Actual vs Predicted Fill Rates\n'
                  f'MAE: {results["mae"]:.4f}, MAPE: {results["mape"]:.2f}%')
    ax1.set_xlabel('Test Period (Days)')
    ax1.set_ylabel('Fill Rate')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Prediction Errors
    errors = np.array(results['actuals']) - np.array(results['predictions'])
    ax2.plot(range(len(errors)), errors, marker='o', color='green', alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.set_title(f'Prediction Errors (Actual - Predicted)')
    ax2.set_xlabel('Test Period (Days)')
    ax2.set_ylabel('Error')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

print(f"\n{'='*60}")
print("RECOMMENDATIONS")
print(f"{'='*60}")
print("""
BASED ON THE VALIDATION ANALYSIS:

1. MODEL PERFORMANCE ASSESSMENT:
   - Compare MAE against business tolerance levels
   - Models with negative improvement need investigation
   - Fill rates > 1.0 are normal (over-filling scenarios)

2. NEGATIVE PREDICTIONS:
   - Address any negative predictions as they're unrealistic
   - Consider log transformation or constrained forecasting

3. NEXT STEPS:
   - Use plot_validation_results(coating_id) to visualize performance
   - Consider ensemble methods if individual models underperform
   - Implement real-time model monitoring and retraining

USAGE:
plot_validation_results(1)  # Visualize results for coating ID 1
""")

print(f"\nTo visualize validation results: plot_validation_results(coating_id)")