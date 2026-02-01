import boto3
import os
import pandas as pd
import pickle


S3_BUCKET = 'unclechris-fuel-forecast-storage'


def load_model():
    # Try grabbing the model from storage local to the lambda func
    try:
        with open('tmp/model.pkl', 'r') as f:
            return pickle.load(f)
    except FileNotFoundError:
        pass

    # Load the model pickle from the s3 bucket
    s3_client = boto3.client('s3')

    resp = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key='model.pkl'
    )
    raw_content = resp['Body'].read()
    os.makedirs('tmp', exist_ok=True)
    with open('tmp/model.pkl', 'wb') as f:
        f.write(raw_content)
    return pickle.loads(raw_content)


def handler(event, context):
    model = load_model()

    df = pd.DataFrame([{
        'day_of_week': 1,
        'is_rising_lag_one': 0,
        'is_falling_lag_one': 0,
        'is_spike_lag_one': 0,
        'days_since_spike_lag_one': 2,
        'yesterdays_price': 100.0,
    }])
    result = float(round(model.predict(df)[0], 2))
    return {
        'statusCode': 200,
        'body': result
    }

if __name__ == '__main__':
    print(handler(None, None))
