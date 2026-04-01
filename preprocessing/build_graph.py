def build_edges(songs, sim_matrix, threshold):
    edges = []
    n = len(songs)

    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i][j]
            if sim >= threshold:
                edges.append({
                    "id1": songs.loc[i, "track_id"],
                    "id2": songs.loc[j, "track_id"],
                    "similarity": round(float(sim), 4)
                })

    return edges