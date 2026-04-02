'''
Name: similarity.py
Contains function for calculating the cosine similarity between songs.
'''

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity_matrix(df, features):
    '''
    Receives a dataframe and list of audio features to compare.
    Normalizes the features to [0, 1] then computes pairwise
    cosine similarity. Only accepts continuous numerical attributes.
    Returns the similarity matrix and normalized feature matrix.
    '''
    scaler = MinMaxScaler()
    feature_matrix = scaler.fit_transform(df[features].fillna(0))
    sim_matrix = cosine_similarity(feature_matrix)
    return sim_matrix, feature_matrix