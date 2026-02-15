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

def get_latest_prices(station_name, fuel_type):
    ddb_client = boto3.client('dynamodb', region_name='ap-southeast-2')
    result = ddb_client.query(
        TableName='fuel_forecast_latest_prices',
        KeyConditions={
            'station_and_fuel_type': {
                'AttributeValueList': [
                    {'S': f'{station_name}|{fuel_type}'}
                ],
                'ComparisonOperator': 'EQ'
            },
        }
    )
    return [{
        'station_and_fuel_type': item['station_and_fuel_type']['S'],
        'date': datetime.datetime.strptime(item['date']['S'], '%d/%m/%Y').date(),
        'price': float(item['price']['N'])
    } for item in result['Items']]

def get_features(date, price_lag_one, price_lag_two):
    return {
        'day_of_week': date.weekday(),
        'is_rising_lag_one': price_lag_one - price_lag_two > 0,
        'is_falling_lag_one': price_lag_one - price_lag_two < 0,
        'yesterdays_price': price_lag_one
    }

def handler(event, context):
    model = load_model()
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    num_days_to_predict = 3
    station_name = event['station_name']
    fuel_type = event['fuel_type']

    latest_prices = get_latest_prices(station_name, fuel_type)
    price_lag_one = [entry for entry in latest_prices if entry['date'] == today][0]['price']
    price_lag_two = [entry for entry in latest_prices if entry['date'] == yesterday][0]['price']
    next_date = today + datetime.timedelta(days=1)
    results = []
    for _ in range(num_days_to_predict):
        input_df = pd.DataFrame([get_features(next_date, price_lag_one, price_lag_two)])
        predicted_price = round(model.predict(input_df)[0], 2)
        price_lag_two = price_lag_one
        price_lag_one = predicted_price
        next_date = next_date + datetime.timedelta(days=1)
        results.append(predicted_price)

    return {
        'statusCode': 200,
        'body': results
    }


if __name__ == '__main__':
    print(handler({
        'station_name': '7-Eleven Toongabbie',
        'fuel_type': 'E10'
    }, None))
