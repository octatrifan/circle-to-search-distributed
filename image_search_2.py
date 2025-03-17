from extract_embeddings import extract_clip_embedding
from metadata_op import find_closest_centroid, find_similar_centroids
import json
import numpy as np

METADATA_FILE = "centroids_metadata.json"


def search_similar_images(image_path, top_k=5, WORKER_ID=1, master_mode=False):
    """Finds the most similar images by searching the closest centroid and performing ANN search."""

    # Step 1: Convert image to embedding
    query_embedding = extract_clip_embedding(image_path)

    # Step 2: Find closest centroid
    closest_centroid, db_file, assigned_worker = find_closest_centroid(query_embedding)
    print(closest_centroid,  db_file, assigned_worker)

    if master_mode:
        # If this function is called by the master, return the assigned worker
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        return closest_centroid, assigned_worker

    # Step 3: Perform the actual search (only if running on a worker node)
    import h5py
    all_candidates = []

    with h5py.File(db_file, "r") as f:
        cluster_embeddings = f[f"embeddings_{closest_centroid}"][:]
        image_paths = f[f"image_paths_{closest_centroid}"][:].astype(str)

    cluster_distances = np.linalg.norm(cluster_embeddings - query_embedding, axis=1)
    top_indices = np.argsort(cluster_distances)[:top_k]

    # Compute similarity scores
    max_cluster_dist = np.max(cluster_distances) if np.max(cluster_distances) > 0 else 1  # Avoid division by zero
    similarity_scores = [float(round((1 - (cluster_distances[i] / max_cluster_dist)) * 100, 1)) for i in top_indices]

    all_candidates.extend([(str(image_paths[i]), similarity_scores[idx]) for idx, i in enumerate(top_indices)])

    return sorted(all_candidates, key=lambda x: -x[1])[:top_k]
