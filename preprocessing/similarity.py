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

    sim_matrix = cosine_similarity(feature_matrix)
    return sim_matrix, feature_matrix

