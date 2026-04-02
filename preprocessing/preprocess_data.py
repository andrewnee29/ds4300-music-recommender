'''
Name: preprocess_data.py
Handles loading and sampling the Spotify CSV.

- All songs by the favorite artists are always included
  in full, since they are the seed artists for recommendation.
- The remaining slots up to the sample size are filled with a random
  sample: 80% from genres already liked, 20% from new genres
  to encourage exploration.
- Duplicates are removed before sampling.
'''
import pandas as pd


def load_and_sample_data(csv_path, sample_size, fav_artists):
    df = pd.read_csv(csv_path)

    # Remove duplicate songs
    df = df.drop_duplicates(subset="track_id")

    # Join artist list into a regex string for str.contains
    artist_pattern = "|".join(fav_artists)
    fav = df[df["artists"].str.contains(artist_pattern, na=False)]

    # Exclude favorite artist songs from the remaining pool
    rest = df[~df["track_id"].isin(fav["track_id"])]

    # Get the genres of the seed artists for guided sampling
    seed_genres = fav["track_genre"].dropna().unique().tolist()

    # Split remaining pool into same-genre and new-genre
    genre_pool = rest[rest["track_genre"].isin(seed_genres)]
    new_genre_pool = rest[~rest["track_genre"].isin(seed_genres)]

    # 80% same genre, 20% new genre from remaining slots
    remaining = sample_size - len(fav)
    liked_genre_n = max(0, int(remaining * 0.8))
    new_genre_n = max(0, remaining - liked_genre_n)

    liked_sample = genre_pool.sample(n=min(liked_genre_n, len(genre_pool)),
                                     random_state=42)
    new_sample = new_genre_pool.sample(n=min(new_genre_n, len(new_genre_pool)),
                                       random_state=42)

    songs = pd.concat([fav, liked_sample, new_sample]).reset_index(drop=True)
    print(f"Found {len(fav)} songs by seed artists")
    print(f"Total songs in graph: {len(songs)}")
    return songs