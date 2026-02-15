import datetime
import logging
import os
import pickle

import boto3
import pandas as pd

# docker buildx build --platform linux/arm64 --provenance=false -t predict_price:latest .
# aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 623791025140.dkr.ecr.ap-southeast-2.amazonaws.com/fuel-price
# docker tag predict_price:latest 623791025140.dkr.ecr.ap-southeast-2.amazonaws.com/fuel-price:latest
# docker push 623791025140.dkr.ecr.ap-southeast-2.amazonaws.com/fuel-price:latest

logger = logging.getLogger()
_model = None


def load_model():
    global _model
    if not _model:
        with open('./model.pkl', 'rb') as f:
            _model = pickle.load(f)
    return _model

def get():
    ddb_client = boto3.client('dynamodb')
    result = ddb_client.get_item(
        TableName='fuel_forecast_latest_prices',
        Key={
            'station_and_fuel_type': {
                'S': 'AVOCA FUEL|E10'
            }
        }
    )

def handler(event, context):
    print('Starting')
    print(os.getcwd())
    print(os.listdir('.'))
    model = load_model()
    print('Finished loading model')
    today = datetime.date.today()
    today.weekday()
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
    # logging.info(handler(None, None))
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    ddb_client = boto3.client('dynamodb', region_name='ap-southeast-2')
    result = ddb_client.get_item(
        TableName='fuel_forecast_latest_prices',
        Key={
            'station_and_fuel_type': {
                'S': 'AVOCA FUEL|E10'
            },
            'date': {
                'S': yesterday.strftime('%d/%m/%Y')
            }
        },
        ReturnConsumedCapacity='TOTAL'
    )
    print(result)