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

S3_BUCKET = 'unclechris-fuel-forecast-storage'

logger = logging.getLogger()


def load_model():
    # Try grabbing the model from storage local to the lambda func
    try:
        with open('/tmp/model.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        pass

    # Load the model pickle from the s3 bucket
    s3_client = boto3.client('s3')

    logger.info('Pulling model from s3')
    resp = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key='model.pkl'
    )
    logger.info('Writing model to /tmp')
    raw_content = resp['Body'].read()
    os.makedirs('/tmp', exist_ok=True)
    with open('/tmp/model.pkl', 'wb') as f:
        f.write(raw_content)
    logger.info('Parsing model')
    model = pickle.loads(raw_content)
    logger.info('Done')
    return model


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
    model = load_model()
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