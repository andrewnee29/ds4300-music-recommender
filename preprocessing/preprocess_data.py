import pandas as pd

def load_and_sample_data(csv_path, sample_size):
    df = pd.read_csv(csv_path)

    # Remove duplicates
    df = df.drop_duplicates(subset="track_id")

    # Keep favorite artists
    fav = df[df["artists"].str.contains("The Strokes|Regina Spektor", na=False)]

    rest = df[~df["track_id"].isin(fav["track_id"])]
    sample_n = max(0, sample_size - len(fav))
    sampled = rest.sample(n=sample_n, random_state=42)

    songs = pd.concat([fav, sampled]).reset_index(drop=True)

    return songs