'''
Name: main.py
run neo4j pipline to build graph!
    1. Load & sample data
    2. Compute similarity
    3. Build edge list
    4. Load into Neo4j
'''
from config import *
from preprocess_data import load_and_sample_data
from similarity import compute_similarity_matrix
from build_graph import build_edges
from neo4j_builder import get_driver, load_all

def main():
    print("Loading & sampling data...")
    songs = load_and_sample_data(CSV_PATH, SAMPLE_SIZE, FAV_ARTISTS)

    print("Computing similarity...")
    sim_matrix, feature_matrix = compute_similarity_matrix(songs, FEATURES)

    print("Building edges...")
    edges = build_edges(songs, sim_matrix, feature_matrix, FEATURES,
                        SIMILARITY_THRESHOLD)

    print("Loading into Neo4j...")
    driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    load_all(driver, songs, edges)
    driver.close()

    print("Done, loaded everything into Neo4J!")

if __name__ == "__main__":
    main()