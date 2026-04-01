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

# ─────────────────────────────────────────────
# HELPER: Run a query and print results
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# QUERY 0: Sanity Checks
# ─────────────────────────────────────────────
def sanity_checks():
    # TODO: count total nodes
    total_songs = run_query("""
        MATCH (s:Song)
        RETURN count(s) as total_songs
    """)
    print_results("Total Songs", total_songs)

    # TODO: count total edges
    total_edges = run_query("""
        MATCH ()-[r:SIMILAR_TO]->()
        RETURN count(r) as total_edges
    """)
    print_results("Total Edges", total_edges)

    # TODO: confirm Strokes songs loaded
    strokes_songs = run_query("""
        MATCH (s:Song)
        WHERE s.artist="The Strokes"
        RETURN s.title, s.artist
    """)
    print_results("The Strokes Songs", strokes_songs)

    # TODO: confirm Regina Spektor songs loaded
    regina_songs = run_query("""
        MATCH (s:Song)
        WHERE s.artist="Regina Spektor"
        RETURN s.title, s.artist
    """)
    print_results("Regina Spektor Songs", regina_songs)

# ─────────────────────────────────────────────
# QUERY 1: Songs Similar to The Strokes
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# QUERY 2: Songs Similar to Regina Spektor
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# QUERY 3: Final Top 5 Recommendations
# Combined score from both artists, filtered and ranked
# ─────────────────────────────────────────────
def final_recommendations():
    results = run_query("""
        // TODO: combine both artists, score candidates,
        //       filter out Strokes + Regina Spektor,
        //       return top 5 with artist, album, title, score
        
        MATCH (s:Song)-[r:SIMILAR_TO]-(candidate:Song)
        WHERE s.artist CONTAINS "Regina Spektor" OR s.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "The Strokes"
        AND NOT candidate.artist CONTAINS "Regina Spektor"
        RETURN candidate.title, candidate.artist, candidate.album, candidate.genre,
               sum(r.similarity) AS score
        ORDER BY score DESC
        LIMIT 5
    """)
    print_results("🎵 Top 5 Recommendations for Prof. Rachlin", results)
    return results

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    sanity_checks()
    strokes_recommendations()
    regina_recommendations()
    final_recommendations()
    driver.close()