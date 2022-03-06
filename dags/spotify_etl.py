import pandas as pd
import psycopg2
import requests
from datetime import datetime
from datetime import timedelta
import json
from sqlalchemy import create_engine

def check_if_valid_data(df: pd.DataFrame) -> bool:
    """
    This function checks if DataFrame have valid data in it. 1) Check if DataFrame is empty,
    2) Check if any primary key is repeated or not. 3) Check if the data have any null value.
    4) Verify if the data extracted comes from the last 24 hours.
    :param df: This is the dataframe to be checked
    """
    # Check if dataframe is empty
    if df.empty:
        print('No songs were downloaded, Finishing execution')
        return False

    # Primary Keys
    if pd.Series(df['played_at']).is_unique:
        pass
    else:
        raise Exception('Primary key check was violated')

    # Check for nulls
    if df.isnull().values.any():
        raise Exception('Null value found')

    # Check that all data are of yesterday's date
#    yesterday = datetime.now() - timedelta(days=1)
#    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

#    timestamps = df['timestamp'].tolist()

#    for timestamp in timestamps:
#        if datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d') > timedelta(days=1):
#            raise Exception('At least one of the returned songs does not come from within the last 24 hours')

#    return True

def run_spotify_etl():
    # Scheme: postgresql://user:password@localhost:5432/database_name
    DATABASE_URI = 'postgresql://airflow:airflow@localhost:5432/airflow'
    TOKEN = 'BQCp5v5a1ZPUbtxGaR0wQ9HgkXu2odr-2pLnJt9bz99CEQzRBFWvL7wLxjkJUjvGxoRRg7Au7sruRyPohQoI6QR3XN58BoJbdqG_xrB7-kjeToF5ofotFz0DpHOAL4iURGYZx-dCFSq1Cncd'
    engine = create_engine(DATABASE_URI)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {token}'.format(token=TOKEN)
    }
    today = datetime.now()
    before = today - timedelta(days=1)
    before_unix_timestamp = int(before.timestamp()) * 1000

    while True:
        r = requests.get('https://api.spotify.com/v1/me/player/recently-played?limit=50&after={time}'.format(
            time=before_unix_timestamp), headers=headers)
        data = r.json()
        if 'error' not in data:
            break

        # TODO: Obtain a new token automatically from Spotify API webpage
        print('here goes a new token')
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=TOKEN)
        }
        today = datetime.now()
        before = today - timedelta(days=1)
        before_unix_timestamp = int(before.timestamp()) * 1000

    song_names = []
    artist_names = []
    played_at_list = []
    timestamps = []

    for song in data['items']:
        song_names.append(song['track']['name'])
        artist_names.append(song['track']['album']['artists'][0]['name'])
        played_at_list.append(song['played_at'])
        timestamps.append(song['played_at'][0:10])

    song_dict = {
        'song_name': song_names,
        'artist_name': artist_names,
        'played_at': played_at_list,
        'timestamp': timestamps
    }

    song_df = pd.DataFrame(song_dict, columns=['song_name', 'artist_name', 'played_at', 'timestamp'])
    print(song_df)
    if check_if_valid_data(song_df):
        print('Data valid, proceed to load stage')

    song_df.to_sql('spotify_data', con=engine, if_exists='replace')
    # song_df.to_sql('spotify_data', con=engine, if_exists='append')
    engine.execute('SELECT * FROM public.spotify_data').fetchall()
    print('Uploading to database completed')