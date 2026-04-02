'''

Filename: query_runner.py
This file is the  final step in the pipeline that actually queries Neo4j
and generates the song recommendations

'''



import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ─────────────────────────────────────────────
# CONFIG — loads from .env file
# ─────────────────────────────────────────────
load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER     = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

#
# Helper function: Run a query and print results
def run_query(query, params=None):
    with driver.session() as session:
        results = session.run(query, params or {})
        return [record.data() for record in results]

def print_results(title, results):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r}")

# QUERY 0: Sanity Checks
def sanity_checks():
    # count total nodes, how many songs are in the db total?
    total_songs = run_query("""
        MATCH (s:Song)
        RETURN count(s) as total_songs
    """)
    print_results("Total Songs", total_songs)

    # How many SIMILAR_TO edges exist?
    total_edges = run_query("""
        MATCH ()-[r:SIMILAR_TO]->()
        RETURN count(r) as total_edges
    """)
    print_results("Total Edges", total_edges)

    # check that Strokes songs loaded
    strokes_songs = run_query("""
        MATCH (s:Song)
        WHERE s.artist="The Strokes"
        RETURN s.title, s.artist
    """)
    print_results("The Strokes Songs", strokes_songs)

    # check that Regina Spektor songs loaded
    regina_songs = run_query("""
        MATCH (s:Song)
        WHERE s.artist="Regina Spektor"
        RETURN s.title, s.artist
    """)
    print_results("Regina Spektor Songs", regina_songs)

    total = run_query("""
        MATCH (s:Song)
        RETURN count(s) AS total, collect(DISTINCT s.artist)[0..10] AS sample_artists
    """)
    print_results("Total Songs and Sample Artists", total)

'''
Query 1: Find songs similar to The Strokes
    Traverses the graph from every Strokes node, 
    follows the SIMILAR_TO edges, then ranks candidates by 
    their total similarity score
'''
def strokes_recommendations():
    results = run_query("""
        // TODO: traverse edges from Strokes songs
        //       to find highly similar candidates
        
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "Regina Spektor"
        RETURN candidate.title, candidate.artist, candidate.album, candidate.genre, 
               sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT 5
    """)
    print_results("Songs Similar to The Strokes", results)
    return results

'''
Query 2: Find songs similar to Regina Spektor
    Traverses the graph from every R.S node, 
    follows the SIMILAR_TO edges, then ranks candidates by 
    their total similarity score

'''
def regina_recommendations():
    results = run_query("""
        // TODO: traverse edges from Regina Spektor songs
        //       to find highly similar candidates
        
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.artist CONTAINS "Regina Spektor"
        AND NOT candidate.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "Regina Spektor"
        RETURN candidate.title, candidate.artist, candidate.album, candidate.genre,
               sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT 5
    """)
    print_results("Songs Similar to Regina Spektor", results)
    return results


'''
Query 3: Gather the final reccomendations:
This query combines both artists and returns the single ranked top 5 list. 
It scores candidates based on similarity to both artists combined, 
meaning songs that are similar to both will rank 
higher than songs that only match one
'''
def final_recommendations():
    results = run_query("""
        // TODO: combine both artists, score candidates,
        //       filter out Strokes + Regina Spektor,
        //       return top 5 with artist, album, title, score
        
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE (s.artist CONTAINS "Regina Spektor" OR s.artist CONTAINS "The Strokes")
        AND NOT candidate.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "Regina Spektor"
        RETURN candidate.title, candidate.artist, candidate.album, candidate.genre,
               sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT 5
    """)
    print_results("🎵 Top 5 Recommendations for Prof. Rachlin", results)
    return results

'''
This proves the general use of our system, below in the driver function feel free 
to test out different songs to receive recommendations
'''
def recommend_any_song(song_title):
    results = run_query("""
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.title CONTAINS $title
        RETURN candidate.title, candidate.artist, sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT 5
    """, {"title": song_title})
    print_results(f"Recommendations based on: {song_title}", results)

def genre_analysis():
    # How many edges stay WITHIN the same genre
    within_genre = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre = candidate.genre
        RETURN s.genre, count(*) AS within_genre_edges
        ORDER BY within_genre_edges DESC
        LIMIT 10
    """)
    print_results("Within-Genre Connections (Top 10)", within_genre)

    # How many edges CROSS between different genres
    cross_genre = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre <> candidate.genre
        RETURN s.genre, candidate.genre, count(*) AS cross_genre_edges
        ORDER BY cross_genre_edges DESC
        LIMIT 10
    """)
    print_results("Cross-Genre Connections (Top 10)", cross_genre)

    # Which genres are most isolated vs most connected to others
    genre_reach = run_query("""
        MATCH (s:Song)-[:SIMILAR_TO]-(candidate:Song)
        WHERE s.genre = candidate.genre
        RETURN s.genre, count(*) AS within_genre_edges
        ORDER BY within_genre_edges DESC
        LIMIT 10
    """)
    print_results("Genre Reach (how many other genres each genre connects to)", genre_reach)


if __name__ == "__main__":
    def list_some_songs():
        results = run_query("""
            MATCH (s:Song)
            WHERE NOT s.artist CONTAINS "The Strokes"
            AND NOT s.artist CONTAINS "Regina Spektor"
            RETURN s.title, s.artist
            LIMIT 20
        """)
        print_results("Sample Songs In Database", results)


    sanity_checks()
    strokes_recommendations()
    regina_recommendations()
    final_recommendations()
    genre_analysis()


    # Prove the system works for any song, not just the Strokes/Regina Spektor
    recommend_any_song("She's Always a Woman")
    recommend_any_song("Piano Man")

    driver.close()