'''
Filename: query_runner.py
This file is the final step in the pipeline that actually queries Neo4j
and generates the song recommendations
'''

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ─────────────────────────────────────────────
# CONFIG — loads from .env file
# ─────────────────────────────────────────────
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Helper function: Run a query and return results as a list of dicts
def run_query(query, params=None):
    with driver.session() as session:
        results = session.run(query, params or {})
        return [record.data() for record in results]

# Helper function: Print results in a readable format
def print_results(title, results):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r}")

# QUERY 0: Sanity Checks
def sanity_checks(artists=None):
    """
    Verifies the graph loaded correctly.
    Optionally pass a list of artists to confirm their songs are in the db.
    Example: sanity_checks(["The Strokes", "Regina Spektor"])
    """
    # Count total number of Song nodes in the graph
    total_songs = run_query("""
        MATCH (s:Song)
        RETURN count(s) as total_songs
    """)
    print_results("Total Songs", total_songs)

    # Count total number of SIMILAR_TO relationships in the graph
    total_edges = run_query("""
        MATCH ()-[r:SIMILAR_TO]->()
        RETURN count(r) as total_edges
    """)
    print_results("Total Edges", total_edges)

    # For each artist, confirm their songs are present in the graph
    if artists:
        for artist in artists:
            songs = run_query(f"""
                MATCH (s:Song)
                WHERE s.artist CONTAINS "{artist}"
                RETURN s.title, s.artist
            """)
            print_results(f"{artist} Songs", songs)

    # Show total song count and a sample of artists in the graph
    total = run_query("""
        MATCH (s:Song)
        RETURN count(s) AS total, collect(DISTINCT s.artist)[0..10] AS sample_artists
    """)
    print_results("Total Songs and Sample Artists", total)


'''
Query 1: Find songs similar to a single artist.
Traverses SIMILAR_TO edges from the given artist's songs,
aggregates similarity scores across all their songs,
and returns the top candidates ranked by total score.
'''
def single_artist_recommendations(artist: str, limit=5):
    results = run_query(f"""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.artist CONTAINS "{artist}"
        AND NOT candidate.artist CONTAINS "{artist}"
        RETURN candidate.title, candidate.artist, candidate.album, candidate.genre,
               sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT {limit}
    """)
    print_results(f"Songs Similar to {artist}", results)
    return results


'''
Query 2: General-purpose multi-artist recommendation function.
Runs one query per artist, normalizes each artist's scores by their
song count in the db, then weights each artist equally regardless
of how many songs they have. This ensures no single artist
dominates the recommendations just because they have more songs.
'''
def get_recommendations(artists: list, limit=5):
    exclude_conditions = " AND ".join(
        [f'NOT candidate.artist CONTAINS "{a}"' for a in artists]
    )

    n = len(artists)
    artist_scores = {}

    for artist in artists:
        # Get total number of songs for this artist in the db
        total = run_query(f"""
            MATCH (s:Song)
            WHERE s.artist CONTAINS "{artist}"
            RETURN count(s) AS total
        """)[0]["total"]

        # Divide by total artist songs (not just connected ones)
        # so songs similar to MORE of the artist's catalog score higher
        query = f"""
            MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
            WHERE s.artist CONTAINS "{artist}"
            AND {exclude_conditions}
            RETURN candidate.track_id, candidate.title, candidate.artist,
                   candidate.album, candidate.genre,
                   sum(r.similarity) / {total} AS score
        """
        results = run_query(query)
        for r in results:
            key = r["candidate.track_id"]
            if key not in artist_scores:
                artist_scores[key] = {"data": r, "total": 0.0}
            artist_scores[key]["total"] += r["score"] / n

    # Build final list — songs only connected to 1 of 2 artists max out at 0.5
    final = []
    for key, val in artist_scores.items():
        entry = val["data"].copy()
        entry["score"] = round(val["total"], 4)
        final.append(entry)

    # Sort by final score and return top N
    final = sorted(final, key=lambda x: x["score"], reverse=True)[:limit]
    print_results(f"Recommendations for {artists}", final)
    return final


'''
Query 3: Final top N recommendations for a list of artists.
Wraps get_recommendations() to produce the final ranked list,
combining similarity scores evenly across all provided artists.
'''
def final_recommendations(artists: list, limit=5):
    results = get_recommendations(artists, limit)
    print_results(f"🎵 Top {limit} Recommendations for {artists}", results)
    return results


def genre_analysis():
    """
    Analyzes the structure of the graph by genre.
    Shows which genres are most interconnected within themselves,
    which genres cross over most to others, and which genres
    have the broadest reach across the graph.
    """
    # Count edges between songs of the same genre
    within_genre = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre = candidate.genre
        RETURN s.genre, count(*) AS within_genre_edges
        ORDER BY within_genre_edges DESC
        LIMIT 10
    """)
    print_results("Within-Genre Connections (Top 10)", within_genre)

    # Count edges between songs of different genres
    cross_genre = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre <> candidate.genre
        RETURN s.genre, candidate.genre, count(*) AS cross_genre_edges
        ORDER BY cross_genre_edges DESC
        LIMIT 10
    """)
    print_results("Cross-Genre Connections (Top 10)", cross_genre)

    # Count how many distinct genres each genre connects to
    genre_reach = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre <> candidate.genre
        RETURN s.genre, count(DISTINCT candidate.genre) AS other_genres_reached
        ORDER BY other_genres_reached DESC
        LIMIT 10
    """)
    print_results("Genre Reach (how many other genres each genre connects to)", genre_reach)


def get_mood_rec(song_title):
    """
    Recommends songs that match the mood of a given song using overall similarity.
    Returns one same-genre match and one cross-genre match,
    showing that mood can transcend genre boundaries.
    """
    # Find the most similar song within the same genre
    same_genre = run_query("""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.title CONTAINS $title
        AND s.genre = candidate.genre
        AND NOT candidate.artist CONTAINS s.artist
        RETURN candidate.title, candidate.artist, candidate.album,
               candidate.genre, round(r.similarity, 4) AS mood_score
        ORDER BY mood_score DESC
        LIMIT 1
    """, {"title": song_title})

    # Find the most similar song from a different genre
    diff_genre = run_query("""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.title CONTAINS $title
        AND s.genre <> candidate.genre
        AND NOT candidate.artist CONTAINS s.artist
        RETURN candidate.title, candidate.artist, candidate.album,
               candidate.genre, round(r.similarity, 4) AS mood_score
        ORDER BY mood_score DESC
        LIMIT 1
    """, {"title": song_title})

    print_results(f"Mood Recommendations for '{song_title}'", same_genre + diff_genre)
    return same_genre + diff_genre


def get_sound_rec(song_title):
    """
    Recommends songs that match the sound texture of a given song using overall similarity.
    Returns one same-genre match and one cross-genre match,
    demonstrating that sonic texture can appear across different genres.
    """
    # Find the most sonically similar song within the same genre
    same_genre = run_query("""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.title CONTAINS $title
        AND s.genre = candidate.genre
        AND NOT candidate.artist CONTAINS s.artist
        RETURN candidate.title, candidate.artist, candidate.album,
               candidate.genre, round(r.similarity, 4) AS sound_score
        ORDER BY sound_score DESC
        LIMIT 1
    """, {"title": song_title})

    # Find the most sonically similar song from a different genre
    diff_genre = run_query("""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.title CONTAINS $title
        AND s.genre <> candidate.genre
        AND NOT candidate.artist CONTAINS s.artist
        RETURN candidate.title, candidate.artist, candidate.album,
               candidate.genre, round(r.similarity, 4) AS sound_score
        ORDER BY sound_score DESC
        LIMIT 1
    """, {"title": song_title})

    print_results(f"Sound Recommendations for '{song_title}'", same_genre + diff_genre)
    return same_genre + diff_genre


if __name__ == "__main__":
    ARTISTS = ["The Strokes", "Regina Spektor"]

    sanity_checks(ARTISTS)
    for artist in ARTISTS:
        single_artist_recommendations(artist)
    final_recommendations(ARTISTS)
    genre_analysis()
    get_mood_rec("Reptilia")
    get_sound_rec("Us")

    driver.close()