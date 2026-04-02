'''
Name: preprocess_data.py
Contains function for calculating the cosine similarity between the songs.
'''

# imports
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

def compute_similarity_matrix(df, features):
    '''The function receives the dataframe df and features that are being
    compared and scales the dataframe accordingly calculates the cosine
    similarity between, it only can receive continuous attributes'''
    scaler = MinMaxScaler()
    feature_matrix = scaler.fit_transform(df[features].fillna(0))
<<<<<<< Updated upstream

    dist_matrix = euclidean_distances(feature_matrix)
    max_dist = dist_matrix.max()

    sim_matrix = 1 - (dist_matrix / max_dist)
    return sim_matrix
=======
    sim_matrix = cosine_similarity(feature_matrix)
    return sim_matrix, feature_matrix
>>>>>>> Stashed changes
