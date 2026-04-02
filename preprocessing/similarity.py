from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances

def compute_similarity_matrix(df, features):
    scaler = MinMaxScaler()
    feature_matrix = scaler.fit_transform(df[features].fillna(0))

    dist_matrix = euclidean_distances(feature_matrix)
    max_dist = dist_matrix.max()

    sim_matrix = 1 - (dist_matrix / max_dist)
    return sim_matrix
