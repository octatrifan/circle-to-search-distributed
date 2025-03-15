import json
import numpy as np

METADATA_FILE = "centroids_metadata.json"

def find_closest_centroid(query_embedding):
    """Finds the closest centroid from metadata."""
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)

    min_distance = float("inf")
    closest_cluster, closest_hdf5 = None, None

    for cluster, data in metadata.items():
        if cluster == "database_free_space":
            continue
        centroid = np.array(data["centroid"])
        distance = np.linalg.norm(query_embedding - centroid)
        if distance < min_distance:
            min_distance = distance
            closest_cluster = cluster
            closest_hdf5 = data["hdf5_file"]

    return closest_cluster, closest_hdf5


def find_similar_centroids(query_embedding):
    """Finds the closest centroids to a given query embedding using a statistical threshold."""
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)

    centroids = np.array([data["centroid"] for data in metadata.values() if "centroid" in data])
    cluster_ids = [key for key in metadata.keys() if "cluster_" in key]
    hdf5_files = [metadata[key]["hdf5_file"] for key in cluster_ids]

    # Compute distances from the query embedding to all centroids
    distances = np.linalg.norm(centroids - query_embedding, axis=1)

    # Determine statistically significant close centroids
    mean_dist = np.mean(distances)
    std_dist = np.std(distances)

    # Select centroids that are within one standard deviation from the minimum distance
    threshold = np.min(distances) + std_dist
    close_indices = [i for i in range(len(distances)) if distances[i] <= threshold]
    close_cluster_ids = [cluster_ids[i] for i in close_indices]
    close_hdf5_files = [hdf5_files[i] for i in close_indices]

    return close_cluster_ids, close_hdf5_files

