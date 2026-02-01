import base64
import os

import boto3
import datetime
import json
import requests
from decimal import Decimal


BASE_URL = 'https://api.onegov.nsw.gov.au'
DDB_TABLE = 'fuel_forecast_latest_prices'


def handler(event, context):
  secrets_client = boto3.client(service_name='secretsmanager', region_name='ap-southeast-2')
  api_key = json.loads(secrets_client.get_secret_value(
    SecretId='refresh_latest_prices_nsw_gov_api_key'
  )['SecretString'])['value']
  api_secret = json.loads(secrets_client.get_secret_value(
    SecretId='refresh_latest_prices_nsw_gov_api_secret'
  )['SecretString'])['value']

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

  print(f'Num items = {len(prices["prices"])}')
  # If a given station + fuel type has been modified multiple times then pick the latest one of these
  price_entries = {}
  for price_entry in prices['prices']:
    servo_name = station_code_map[str(price_entry['stationcode'])]
    fuel_type = price_entry['fueltype']
    key_name = f'{servo_name}|{fuel_type}'
    if key_name in price_entries:
      old_item_timestamp = datetime.datetime.strptime(price_entries[key_name]['lastupdated'], '%d/%m/%Y %H:%M:%S')
      new_item_timestamp = datetime.datetime.strptime(price_entry['lastupdated'], '%d/%m/%Y %H:%M:%S')
      if new_item_timestamp > old_item_timestamp:
        print(
          f'Replaced key {key_name} as new item has timestamp {new_item_timestamp} compared with {old_item_timestamp}')
        price_entries[key_name] = price_entry
      else:
        print(
          f'Ignored new entry on {key_name} as new item has timestamp {new_item_timestamp} compared with {old_item_timestamp}')
    else:
      price_entries[key_name] = price_entry

  print(f'Num items in price_entries = {len(price_entries)}')

  ddb = boto3.resource('dynamodb', region_name='ap-southeast-2')
  ddb_table = ddb.Table(DDB_TABLE)
  today = datetime.datetime.combine(datetime.date.today(), datetime.time())
  today_formatted = today.strftime('%d/%m/%Y')
  ttl = round((today + datetime.timedelta(days=4)).timestamp())
  num_processed = 0
  with ddb_table.batch_writer() as batch:
    for key_name, price_entry in price_entries.items():
      price = Decimal(str(price_entry['price']))
      batch.put_item(Item={
        'station_and_fuel_type': key_name,
        'date': today_formatted,
        'price': price,
        'ttl': ttl,
      })
      num_processed += 1

  return {
    'statusCode': 200,
    'body': {
      'num_processed': num_processed
    }
  }




# prices = {
#   'stations': [
#     {'code': '1', 'name': 'Test1'},
#     {'code': '2', 'name': 'Test2'},
#   ],
#   'prices': [
#     {'fueltype': 'DL', 'lastupdated': '23/01/2026 05:45:45', 'price': 187.9, 'state': 'NSW', 'stationcode': 1},
#     {'fueltype': 'E10', 'lastupdated': '23/01/2026 05:45:45', 'price': 187.9, 'state': 'NSW', 'stationcode': 1},
#     {'fueltype': 'E10', 'lastupdated': '23/01/2026 05:45:45', 'price': 187.9, 'state': 'NSW', 'stationcode': 2},
#   ]
# }

if __name__ == "__main__":
  handler(None, None)