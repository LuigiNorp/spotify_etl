import pandas as pd
import psycopg2
import requests
from datetime import datetime
from datetime import timedelta
import json
from sqlalchemy import create_engine

# Scheme: postgresql://user:password@localhost:5432/database_name
DATABASE_URI = open('./misc/postgres_conection.txt').readline().strip()
TOKEN = open('./misc/token.txt').readline().strip()
engine = create_engine(DATABASE_URI)


def check_if_valid_data(df: pd.DataFrame) -> bool:
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
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    timestamps = df['timestamp'].tolist()

    for timestamp in timestamps:
        if datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d') > timedelta(days=1):
            raise Exception('At least one of the returned songs does not come from within the last 24 hours')

    return True


if __name__ == '__main__':
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

        with open('./misc/token.txt', 'w') as file:
            TOKEN = input('Please write a new token')
            file.write(TOKEN)
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