import pandas as pd
from statsmodels.tsa.api import ExponentialSmoothing
import warnings


def timesheet_forecasting(sql_result):

    # checking if sql_result has 3 columns or not
    if len(sql_result[0]) == 3:
        data = pd.DataFrame(sql_result, columns=["month_date", "responsible", "sum"])
        
        # Forecasting for each data
        forecast_periods = 12  # Forecasting for the next 12 months
        forecast_results = []

        for name, total in data.groupby('responsible'):

            if len(total) >= 2:
                try:
                    model_total = ExponentialSmoothing(
                        total['sum'].astype(float), trend='add', seasonal='add', seasonal_periods=12)
                    model_fit_total = model_total.fit()
                
                except Exception as e:
                    warnings.warn(f"Error for product {name} when adding seasonality: {str(e)}")

                    model_total = ExponentialSmoothing(
                        total['sum'].astype(float), trend='add', seasonal_periods=12)
                    model_fit_total = model_total.fit()
                
                forecast_values_total = model_fit_total.forecast(steps=forecast_periods).tolist()

                # Generate the date range for the forecast (next 12 months)
                last_date = data['month_date'].max()
                forecast_dates = pd.date_range(
                    start=last_date, periods=forecast_periods, freq='MS')

                # Create a list of dictionaries to store the forecast results for the current data
                forecast_dicts = []
                for i in range(forecast_periods):
                    forecast_dict = {
                        'Month': forecast_dates[i],
                        'Responsible': name,
                        'Total': forecast_values_total[i],
                    }
                    forecast_dicts.append(forecast_dict)
                
                # Append the current data's forecast dictionaries to the list
                forecast_results.extend(forecast_dicts)

            else:
                print(f"Skipping data with id {name} due to insufficient data points.")

        return forecast_results

    else:
        data = pd.DataFrame(sql_result, columns=["month_date", "sum"])

        # Forecasting for each data
        forecast_periods = 12  # Forecasting for the next 12 months
        forecast_results = []

        if(len(data)) >= 2:

            # seasonal forecasting if enough data
            try:
                model_total = ExponentialSmoothing(
                    data['sum'].astype(float), trend='add', seasonal='add', seasonal_periods=12)
                model_fit_total = model_total.fit()
            
            except Exception as e:
                warnings.warn(f"Error for product {data} when adding seasonality: {str(e)}")

                model_total = ExponentialSmoothing(
                    data['sum'].astype(float), trend='add', seasonal_periods=12)
                model_fit_total = model_total.fit()

        
            forecast_values_total = model_fit_total.forecast(steps=forecast_periods).tolist()

            # Generate the date range for the forecast (next 12 months)
            last_date = data['month_date'].max()
            forecast_dates = pd.date_range(
                start=last_date, periods=forecast_periods, freq='MS')

            
            # Create a list of dictionaries to store the forecast results for the current data
            forecast_dicts = []
            for i in range(forecast_periods):
                forecast_dict = {
                    'Month': forecast_dates[i],
                    'Total': forecast_values_total[i],
                }
                forecast_dicts.append(forecast_dict)
            
            # Append the current data's forecast dictionaries to the list
            forecast_results.extend(forecast_dicts)
    
        else:
            print(f"Skipping data due to insufficient data points.")
        
        return forecast_results
        