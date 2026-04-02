'''
Name: preprocess_data.py
Handles loading and sampling the Spotify CSV.

- all songs by the album selected are always included
  in full, since they are the seed artists for recommendation.
- The remaining slots up to pre-determined sample size are filled with a random
  sample from the rest of the dataset, 80 percent are of the genre already liked,
  20 percent are from a new genre to encourage exploration.
- duplicates are removed before sampling.
'''
import pandas as pd

def load_and_sample_data(csv_path, sample_size, fav_artists):
    df = pd.read_csv(csv_path)

    # Remove duplicates
    df = df.drop_duplicates(subset="track_id")

    # ensure the favorite artists songs are sampled
    fav = df[df["artists"].str.contains(fav_artists, na=False)]

    # include all songs by the artist in sample
    rest = df[~df["track_id"].isin(fav["track_id"])]

    # get seed artist genres
    seed_genres = fav["track_genre"].dropna().unique().tolist()

    # split rest into genre-liked and new-genre samples
    genre_pool = rest[rest["track_genre"].isin(seed_genres)]
    new_genre_pool = rest[~rest["track_genre"].isin(seed_genres)]

    # 80/20 split of remaining slots after seed artists are included
    remaining = sample_size - len(fav)
    liked_genre_sample_n = max(0, int(remaining * 0.8))
    new_genre_sample_n = max(0, remaining - liked_genre_sample_n)

    # sample from each pool
    liked_sample = genre_pool.sample(n=min(liked_genre_sample_n, len(genre_pool)),
                                     random_state=42)
    new_sample = new_genre_pool.sample(n=min(new_genre_sample_n, len(new_genre_pool)),
                                       random_state=42)

    songs = pd.concat([fav, liked_sample, new_sample]).reset_index(drop=True)

    return songs
