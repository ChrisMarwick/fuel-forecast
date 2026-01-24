import pandas as pd
import pickle


with open('ml/model.pkl', 'rb') as f:
    model = pickle.load(f)

df = pd.DataFrame([{
    'day_of_week': 1,
    'is_rising_lag_one': 0,
    'is_falling_lag_one': 0,
    'is_spike_lag_one': 0,
    'days_since_spike_lag_one': 2
}])
print(model.predict(df))
