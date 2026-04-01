import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances
from neo4j import GraphDatabase

# ─────────────────────────────────────────────
# CONFIG — loads from .env file
# ─────────────────────────────────────────────
load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER     = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
CSV_PATH       = "/Users/abigailvalladolid/Documents/DS4300/ds4300-music-recommender/data/spotify.csv"
SAMPLE_SIZE    = 1000
SIMILARITY_THRESHOLD = 0.25  # lower = stricter, higher = more edges

# ─────────────────────────────────────────────
# STEP 1: LOAD & SAMPLE DATA
# ─────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)

# Clean up: drop duplicates by track_id
df = df.drop_duplicates(subset="track_id")

# Grab ALL Strokes and Regina Spektor songs first
fav_artists = df[df["artists"].str.contains("The Strokes|Regina Spektor", na=False)]
print(f"Found {len(fav_artists)} songs by The Strokes / Regina Spektor")

# Sample remaining songs from the rest of the dataset
rest = df[~df["track_id"].isin(fav_artists["track_id"])]
sample_size = max(0, SAMPLE_SIZE - len(fav_artists))
sampled = rest.sample(n=sample_size, random_state=42)

# Combine into final working dataset
songs = pd.concat([fav_artists, sampled]).reset_index(drop=True)
print(f"Total songs in graph: {len(songs)}")

# ─────────────────────────────────────────────
# STEP 2: COMPUTE SIMILARITY
# Audio features used for similarity scoring
# ─────────────────────────────────────────────
FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo"
]

# Normalize all features to [0, 1] so tempo doesn't dominate
scaler = MinMaxScaler()
feature_matrix = scaler.fit_transform(songs[FEATURES].fillna(0))

# Compute pairwise Euclidean distances
print("Computing pairwise distances (this may take a moment)...")
dist_matrix = euclidean_distances(feature_matrix)

# Convert distances to similarity scores (1 = identical, 0 = very different)
max_dist = dist_matrix.max()
sim_matrix = 1 - (dist_matrix / max_dist)

# ─────────────────────────────────────────────
# STEP 3: BUILD EDGE LIST
# Connect two songs if similarity >= threshold
# ─────────────────────────────────────────────
print("Building edge list...")
edges = []
n = len(songs)
for i in range(n):
    for j in range(i + 1, n):
        sim = sim_matrix[i][j]
        if sim >= SIMILARITY_THRESHOLD:
            edges.append({
                "id1": songs.loc[i, "track_id"],
                "id2": songs.loc[j, "track_id"],
                "similarity": round(float(sim), 4)
            })

print(f"Total edges to create: {len(edges)}")

# ─────────────────────────────────────────────
# STEP 4: LOAD INTO NEO4J
# ─────────────────────────────────────────────
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def load_songs(tx, batch):
    tx.run("""
        UNWIND $songs AS s
        MERGE (song:Song {track_id: s.track_id})
        SET song.title        = s.track_name,
            song.artist       = s.artists,
            song.album        = s.album_name,
            song.genre        = s.track_genre,
            song.popularity   = s.popularity,
            song.danceability = s.danceability,
            song.energy       = s.energy,
            song.valence      = s.valence,
            song.tempo        = s.tempo,
            song.acousticness = s.acousticness
    """, songs=batch)

def load_edges(tx, batch):
    tx.run("""
        UNWIND $edges AS e
        MATCH (a:Song {track_id: e.id1})
        MATCH (b:Song {track_id: e.id2})
        MERGE (a)-[r:SIMILAR_TO]->(b)
        SET r.similarity = e.similarity
    """, edges=batch)

# Load songs in batches of 500
print("Loading songs into Neo4j...")
song_records = songs.fillna("").to_dict("records")
batch_size = 500
with driver.session() as session:
    for i in range(0, len(song_records), batch_size):
        session.execute_write(load_songs, song_records[i:i+batch_size])
        print(f"  Loaded songs {i} to {min(i+batch_size, len(song_records))}")

# Load edges in batches of 1000
print("Loading edges into Neo4j...")
with driver.session() as session:
    for i in range(0, len(edges), 1000):
        session.execute_write(load_edges, edges[i:i+1000])
        print(f"  Loaded edges {i} to {min(i+1000, len(edges))}")

print("✅ Done! Graph loaded into Neo4j.")
driver.close()