'''
Name: config.py
Central configuration file fo the music recommender.
All shared constants, credentials, and feature definitions are stored here
'''
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER     = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# replace with your CSV path
CSV_PATH = "/Users/kathleenlautenbach/Desktop/DS4300/ds4300-music-recommender/data/spotify.csv"

# feel free to change if needed!
SAMPLE_SIZE = 1000
SIMILARITY_THRESHOLD = 0.5

FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness",
    "valence", "tempo"
]


# customize by entering any artist/artists to the list
ARTISTS = ["The Strokes", "Regina Spektor"]