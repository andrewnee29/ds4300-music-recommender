'''
Name: similarity.py
Contains function for calculating the cosine similarity between the songs.
Filename: query_runner.py
This file is the final step in the pipeline that actually queries Neo4j
and generates the song recommendations
'''

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

def compute_similarity_matrix(df, features):
    '''The function receives the dataframe df and features that are being
    compared and scales the dataframe accordingly calculates the cosine
    similarity between, it only can receive continuous attributes'''
    scaler = MinMaxScaler()
    feature_matrix = scaler.fit_transform(df[features].fillna(0))

    sim_matrix = cosine_similarity(feature_matrix)
    return sim_matrix, feature_matrix