'''
Name: build_graph.py
build the edges of the graph between each song
'''
import numpy as np

def build_edges(songs, sim_matrix, feature_matrix, features, threshold):
    '''builds edge for every paring of songs if the songs match the similiarity threshold
    and saves each feature similarity score individually'''
    edges = []
    n = len(songs)

    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i][j]
            if sim >= threshold:
                edge = {
                    "id1": songs.loc[i, "track_id"],
                    "id2": songs.loc[j, "track_id"],
                    "similarity": round(float(sim_matrix[i][j]), 4)
                }
                for k, feat in enumerate(features):
                    edge[f"{feat}_sim"] = round(
                        float(1 - abs(feature_matrix[i][k] - feature_matrix[j][k])), 4)
                edges.append(edge)

    return edges

