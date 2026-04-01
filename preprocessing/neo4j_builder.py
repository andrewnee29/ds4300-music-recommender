from neo4j import GraphDatabase

def get_driver(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))


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


def load_all(driver, songs, edges):
    song_records = songs.fillna("").to_dict("records")

    total_songs = len(song_records)
    total_edges = len(edges)

    print(f"Total songs: {total_songs}")
    print(f"Total edges: {total_edges}")

    # ───────── SONGS ─────────
    with driver.session() as session:
        for i in range(0, total_songs, 500):
            batch = song_records[i:i+500]
            session.execute_write(load_songs, batch)

            print(f"Loaded songs {i + len(batch)}/{total_songs}")

    # ───────── EDGES ─────────
    with driver.session() as session:
        for i in range(0, total_edges, 1000):
            batch = edges[i:i+1000]
            session.execute_write(load_edges, batch)

            print(f"Loaded edges {i + len(batch)}/{total_edges}")