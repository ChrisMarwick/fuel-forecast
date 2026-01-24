import pandas as pd
from pandas.testing import assert_frame_equal

from ml.model import cleaned_fuelcheck_historic_data


class TestModel:

    def test_cleaned_fuelcheck_historic_data(self):
        station1_details = {
            'ServiceStationName': 'Station 1',
            'Address': '1 Test Road',
            'Suburb': 'Testville',
            'Postcode': '2000',
            'Brand': 'Caltex',
        }
        station1_details_renamed = {
            'servo_name': 'Station 1',
            'address': '1 Test Road',
            'suburb': 'Testville',
            'postcode': '2000',
            'brand': 'Caltex',
        }
        station2_details = {
            'ServiceStationName': 'Station 2',
            'Address': '2 Test Road',
            'Suburb': 'Testville',
            'Postcode': '2000',
            'Brand': 'Caltex',
        }
        station2_details_renamed = {
            'servo_name': 'Station 2',
            'address': '2 Test Road',
            'suburb': 'Testville',
            'postcode': '2000',
            'brand': 'Caltex',
        }
        csv_data = pd.DataFrame([
            {
                **station1_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-01 02:17:21',
                'Price': 200.0
            },
            {
                **station1_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-01 04:17:21',
                'Price': 250.0
            },
            {
                **station1_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-04 02:17:21',
                'Price': 100.0
            },
            {
                **station1_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-06 02:17:21',
                'Price': 50.0
            },
            {
                **station1_details,
                'FuelCode': 'Premium Unleaded',
                'PriceUpdatedDate': '2025-01-01 02:17:21',
                'Price': 400.0
            },
            {
                **station2_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-01 02:17:21',
                'Price': 300.0
            },
            {
                **station2_details,
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-03 02:17:21',
                'Price': 200.0
            },
        ])
        expected = pd.DataFrame([
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-01'),
                'price': 225.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-02'),
                'price': 225.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-03'),
                'price': 225.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-04'),
                'price': 100.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-05'),
                'price': 100.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-06'),
                'price': 50.0
            },
            {
                **station1_details_renamed,
                'fuel_code': 'Premium Unleaded',
                'date': pd.to_datetime('2025-01-01'),
                'price': 400.0
            },
            {
                **station2_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-01'),
                'price': 300.0
            },
            {
                **station2_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-02'),
                'price': 300.0
            },
            {
                **station2_details_renamed,
                'fuel_code': 'E10',
                'date': pd.to_datetime('2025-01-03'),
                'price': 200.0
            },
        ])
        empty_df = pd.DataFrame(columns=[
                'ServiceStationName', 'Address', 'Suburb', 'Postcode', 'Brand', 'FuelCode', 'PriceUpdatedDate',
                'Price'])
        output = cleaned_fuelcheck_historic_data(
            csv_data,
            empty_df
        )
        assert_frame_equal(output, expected, check_like=True)

    def test_cleaned_fuelcheck_historic_data_2(self):
        csv_data = pd.DataFrame([
            {
                'ServiceStationName': 'Station 1',
                'Address': '1 Test Road',
                'Suburb': 'Testville',
                'Postcode': '2000',
                'Brand': 'Caltex',
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-01-01 02:17:21',
                'Price': 200.0
            },
            {
                'ServiceStationName': 'Station 1',
                'Address': '1 Test Road',
                'Suburb': 'Testville',
                'Postcode': '2000',
                'Brand': 'Caltex',
                'FuelCode': 'E10',
                'PriceUpdatedDate': '2025-03-15 02:17:21',
                'Price': 100.0
            },
        ])
        empty_df = pd.DataFrame(columns=[
            'ServiceStationName', 'Address', 'Suburb', 'Postcode', 'Brand', 'FuelCode', 'PriceUpdatedDate',
            'Price'])
        output = cleaned_fuelcheck_historic_data(
            csv_data,
            empty_df
        )
        print(output)
        # assert_frame_equal(output, expected, check_like=True)