'''
Name: preprocess_data.py
Handles loading and sampling the Spotify CSV.

- all songs by the album selected are always included
  in full, since they are the seed artists for recommendation.
- The remaining slots up to pre-determined sample size are filled with a random
  sample from the rest of the dataset, ensuring broad genre coverage.
- duplicates are removed before sampling.
'''
import pandas as pd

def load_and_sample_data(csv_path, sample_size, fav_songs):
    df = pd.read_csv(csv_path)

    # Remove duplicates
    df = df.drop_duplicates(subset="track_id")

    # Keep favorite artists
    fav = df[df["artists"].str.contains(fav_songs, na=False)]

    rest = df[~df["track_id"].isin(fav["track_id"])]
    sample_n = max(0, sample_size - len(fav))
    sampled = rest.sample(n=sample_n, random_state=42)

    songs = pd.concat([fav, sampled]).reset_index(drop=True)

    return songs