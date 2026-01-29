import datetime
from typing import cast, BinaryIO

import pandas as pd
from flypipe import node
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder, StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.compose import ColumnTransformer
from sklearn import set_config
from sklearn.metrics import mean_squared_error
from sklearn.decomposition import PCA
from sklearn.feature_selection import RFE
import pickle


set_config(transform_output='pandas')


DATA_DIR = '.'
# From https://data.nsw.gov.au/data/dataset/fuel-check
DATA_FILES = [
    'price_history_checks_jan2025.csv',
    'price_history_checks_feb2025.csv',
    'fuelcheck_pricehistory_mar25.xlsx',
    'fuelcheck_pricehistory_apr2025.xlsx',
]
DATETIME_FORMATS = (
    '%d/%m/%Y %H:%M',
    '%Y-%m-%d %H:%M:%S'
)

@node(
    type='pandas'
)
def fuelcheck_historic_data_csv():
    output = None
    files = [file for file in DATA_FILES if file.endswith('csv')]
    for filename in files:
        df = pd.read_csv(f'{DATA_DIR}/{filename}')
        if output is None:
            output = df
        else:
            output = pd.concat([output, df])

    return output

@node(
    type='pandas'
)
def fuelcheck_historic_data_excel():
    output = None
    files = [file for file in DATA_FILES if file.endswith('xlsx')]
    for filename in files:
        df = pd.read_excel(f'{DATA_DIR}/{filename}')
        if output is None:
            output = df
        else:
            output = pd.concat([output, df])

    return output

@node(
    type='pandas',
    dependencies=[
        fuelcheck_historic_data_csv.alias('csv_data'),
        fuelcheck_historic_data_excel.alias('excel_data'),
    ]
)
def cleaned_fuelcheck_historic_data(csv_data, excel_data):
    # TODO cache this information in a file maybe?
    csv_data['PriceUpdatedDate'] = pd.to_datetime(csv_data['PriceUpdatedDate'], format='%Y-%m-%d %H:%M:%S')
    excel_data['PriceUpdatedDate'] = pd.to_datetime(excel_data['PriceUpdatedDate'], format='%d/%m/%Y %H:%M')

    df = (
        pd.concat([csv_data, excel_data])
            .rename(columns={
                'ServiceStationName': 'servo_name',
                'Address': 'address',
                'Suburb': 'suburb',
                'Postcode': 'postcode',
                'Brand': 'brand',
                'FuelCode': 'fuel_code',
                'PriceUpdatedDate': 'date',
                'Price': 'price'
            }
        )
    )
    # Get rid of the time component, we don't care about this
    df['date'] = df['date'].dt.normalize()
    # Down/upscale by date to a) average the fuel price between samples on the same day and b) impute missing days with
    # fuel price as the value of the previous day

    df = df.sort_values(['servo_name', 'fuel_code']).reset_index(drop=True)

    df = df.groupby(['servo_name', 'fuel_code']).resample('D', on='date').agg({
        'address': 'first',
        'suburb': 'first',
        'postcode': 'first',
        'brand': 'first',
        'price': 'mean',
    }).ffill().reset_index()
    return df


if __name__ == '__main__':

    # df = cleaned_fuelcheck_historic_data.run()
    # df.to_csv('aggregated.csv')
    df = pd.read_csv('aggregated.csv')
    # df = df[(df['servo_name'] == 'BP Seven Hills') & (df['fuel_code'] == 'E10')]
    df = df[df['fuel_code'] == 'E10']

    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.month == 1]  # TODO remove me

    df['day_of_week'] = df['date'].dt.dayofweek
    df['yesterdays_price'] = df['price'].shift(1).fillna(0)
    df['is_rising'] = df['price'] > df['yesterdays_price']
    df['is_rising_lag_one'] = df['is_rising'].shift(1).fillna(0)
    df['is_falling'] = df['price'] < df['yesterdays_price']
    df['is_falling_lag_one'] = df['is_falling'].shift(1).fillna(0)
    df['percentage_rise'] = (df['price'] - df['yesterdays_price']) / df['yesterdays_price']
    df['is_spike'] = df['percentage_rise'] > 0.1
    df['is_spike_lag_one'] = df['is_spike'].shift(1).fillna(0)

    groups = (df['is_spike']).cumsum()
    df['days_since_spike'] = df.groupby(groups).cumcount()
    df['days_since_spike_lag_one'] = df['days_since_spike']

    categorical_encoder = OrdinalEncoder()
    standard_scaler = StandardScaler()
    preprocessor = ColumnTransformer(
        transformers=[
            ('categorical_encoder', categorical_encoder, ['day_of_week']),
            ('standard_scaler', standard_scaler, ['days_since_spike_lag_one']),
        ],
        remainder='passthrough',
        verbose_feature_names_out=False,
    )
    df = preprocessor.fit_transform(df)


    df = df[['day_of_week', 'is_rising_lag_one', 'is_falling_lag_one', 'is_spike_lag_one', 'days_since_spike_lag_one', 'yesterdays_price', 'price']]
    # df = df[['is_falling_lag_one', 'days_since_spike_lag_one', 'price']]
    # df = df[['day_of_week', 'price']]
    train, other = train_test_split(df, train_size=0.7, test_size=0.3)
    validate, test = train_test_split(df, train_size=0.5, test_size=0.5)
    train['category'] = 'train'
    validate['category'] = 'validate'
    test['category'] = 'test'
    df = pd.concat([train, test, validate]).reset_index(drop=True)

    train = df[df['category'] == 'train'].drop(columns='category')
    validate = df[df['category'] == 'validate'].drop(columns='category')
    test = df[df['category'] == 'test'].drop(columns='category')

    model = SVR()
    model.fit(train.drop(columns=['price']), train[['price']])

    validate['predicted_price'] = model.predict(validate.drop(columns=['price']))
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)

    # mse?
    validate['absolute_residual_error'] = (validate['predicted_price'] - validate['price']).abs()

    great_results = len(validate[validate['absolute_residual_error'] < 5])
    good_results = len(validate[validate['absolute_residual_error'] < 10])
    average_results = len(validate[validate['absolute_residual_error'] < 20])
    print(f'{great_results=} ({round(great_results / len(validate), 2)})')
    print(f'{good_results=} ({round(good_results / len(validate), 2)})')
    print(f'{average_results=} ({round(average_results / len(validate), 2)})')

    rfe = RFE(estimator=LinearRegression(), n_features_to_select=2)
    rfe.fit(train.drop(columns=['price']), train[['price']])
    print(rfe.ranking_)

    # fig, ax = plt.subplots()
    # ax.plot(df['date'], df['price'])
    # ax.scatter(df['date'], df['price'])
    # plt.show()
