import base64

import boto3
import datetime
import json
import requests
from decimal import Decimal
from dotenv import load_dotenv



def handler(event, context):

  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Lambda!')
  }


BASE_URL = 'https://api.onegov.nsw.gov.au'
DDB_TABLE = 'fuel_forecast_latest_prices'

# TODO: pass this via env var
api_key = ''
api_secret = ''
authorization_secret = base64.b64encode(f'{api_key}:{api_secret}'.encode('utf-8')).decode('utf-8')
authorization_secret = f'Basic {authorization_secret}'

resp = requests.get(
  f'{BASE_URL}/oauth/client_credential/accesstoken',
  headers={'Authorization': authorization_secret},
  params={'grant_type': 'client_credentials'}
)
access_token = resp.json()['access_token']

resp = requests.get(
  f'{BASE_URL}/FuelPriceCheck/v2/fuel/prices',
  headers={
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'apikey': '1MYSRAx5yvqHUZc6VGtxix6oMA2qgfRT',
    'transactionid': datetime.date.today().strftime('%d/%m/%Y'),
    'requesttimestamp': datetime.datetime(2026, 1, 26).strftime('%d/%m/%Y %I:%M:%S %p')
  }
)
prices = resp.json()

station_code_map = {
  station['code']: station['name'] for station in prices['stations']
}
for price_entry in prices['prices']:
  servo_name = station_code_map[price_entry['stationcode']]
  fuel_type = price_entry['fueltype']
  price = price_entry['price']
  put_item

def put_item():
  # Handle the batching under the hood

ddb = boto3.resource('dynamodb', region_name='ap-southeast-2')
today = datetime.datetime.combine(datetime.date.today(), datetime.time())
ttl = round((today + datetime.timedelta(days=4)).timestamp())
table = ddb.Table('fuel_forecast_latest_prices')
table.put_item(
  Item={
    'station_and_fuel_type': 'bla',
    'date': datetime.date.today().strftime('%d/%m/%Y'),
    'price': Decimal('50.5'),
    'ttl': ttl
  }
)
