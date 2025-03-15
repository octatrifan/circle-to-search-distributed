from extract_embeddings import extract_clip_embedding
from metadata_op import find_closest_centroid, find_similar_centroids
import json
import h5py
import numpy as np
from PIL import Image
import torch

METADATA_FILE = "centroids_metadata.json"

def search_similar_images(image_path, top_k=5):
    """Finds the most similar images by searching the closest centroid and performing ANN search."""
    query_embedding = extract_clip_embedding(image_path)
    close_cluster_ids, close_hdf5_files = find_similar_centroids(query_embedding)

    all_candidates = []

    # Search within each close cluster
    for cluster_id, db_file in zip(close_cluster_ids, close_hdf5_files):
        with h5py.File(db_file, "r") as f:
            cluster_embeddings = f[f"embeddings_{cluster_id}"][:]
            image_paths = f[f"image_paths_{cluster_id}"][:].astype(str)

        cluster_distances = np.linalg.norm(cluster_embeddings - query_embedding, axis=1)
        top_indices = np.argsort(cluster_distances)[:top_k]

        max_cluster_dist = np.max(cluster_distances) if np.max(cluster_distances) > 0 else 1  # Avoid division by zero
        similarity_scores = [float(round((1 - (cluster_distances[i] / max_cluster_dist)) * 100, 1)) for i in
                             top_indices]

        all_candidates.extend([(str(image_paths[i]), similarity_scores[idx]) for idx, i in enumerate(top_indices)])

    # Sort overall top-k images based on similarity scores
    all_candidates.sort(key=lambda x: -x[1])  # Sort by highest similarity score

    return all_candidates[:top_k]

# Test the script
image_path = "101_ObjectCategories/airplanes/image_0001.jpg"
similar_images = search_similar_images(image_path)
print(similar_images)
