import os
import h5py
import json
import numpy as np
from sklearn.cluster import KMeans

# Configuration
NUM_CLUSTERS = 10  # Initial 10-Means Clustering
NUM_DATABASES = 5  # Number of database instances
MAX_DB_CAPACITY = 1000  # Max images per database instance
SPLIT_THRESHOLD = 500  # If cluster has more than this, apply recursive 2-Means
EMBEDDINGS_FILE = "image_embeddings.npy"
IMAGE_PATHS_FILE = "image_paths.txt"
OUTPUT_METADATA = "centroids_metadata.json"


def load_data():
    """Loads embeddings and image paths."""
    embeddings = np.load(EMBEDDINGS_FILE)
    with open(IMAGE_PATHS_FILE, "r") as f:
        image_paths = [line.strip() for line in f.readlines()]
    return embeddings, image_paths


def perform_clustering(embeddings, num_clusters):
    """Performs K-Means clustering and returns cluster assignments and centroids."""
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    centroids = kmeans.cluster_centers_
    return labels, centroids


def recursively_split_cluster(embeddings, image_paths, indices, clusters, centroids):
    """Recursively splits clusters larger than SPLIT_THRESHOLD using 2-Means clustering."""
    if len(indices) <= SPLIT_THRESHOLD:
        cluster_id = len(clusters)
        clusters[cluster_id] = (indices, [image_paths[idx] for idx in indices])
        centroids.append(np.mean(embeddings[indices], axis=0))
        return

    sub_labels, sub_centroids = perform_clustering(embeddings[indices], 2)
    for sub in range(2):
        sub_indices = indices[sub_labels == sub]
        if len(sub_indices) <= SPLIT_THRESHOLD:
            cluster_id = len(clusters)
            clusters[cluster_id] = (sub_indices, [image_paths[idx] for idx in sub_indices])
            centroids.append(sub_centroids[sub])
        else:
            recursively_split_cluster(embeddings, image_paths, sub_indices, clusters, centroids)


def split_large_clusters(embeddings, image_paths, labels, centroids):
    """Handles the initial clustering and recursively splits large clusters."""
    clusters = {}
    new_centroids = []

    for i in range(len(centroids)):
        indices = np.where(labels == i)[0]
        recursively_split_cluster(embeddings, image_paths, indices, clusters, new_centroids)

    return clusters, np.array(new_centroids)


def distribute_clusters(clusters, embeddings, centroids):
    """Distributes clusters across databases and assigns workers based on DB file."""
    os.makedirs("hdf5_files", exist_ok=True)
    database_free_space = {f"hdf5_files/db_{i}.h5": MAX_DB_CAPACITY for i in range(NUM_DATABASES)}

    # Mapping database files to workers
    worker_mapping = {
        "hdf5_files/db_0.h5": "worker1",
        "hdf5_files/db_1.h5": "worker2",
        "hdf5_files/db_2.h5": "worker3",
        "hdf5_files/db_3.h5": "worker4",
        "hdf5_files/db_4.h5": "worker5",

    }

    cluster_metadata = {"database_free_space": database_free_space.copy()}

    for cluster_id, (indices, paths) in sorted(clusters.items(), key=lambda x: -len(x[1][0])):
        best_db = max(database_free_space, key=database_free_space.get)

        if database_free_space[best_db] >= len(indices):
            assigned_worker = worker_mapping[best_db]  # Choose worker based on file name

            cluster_metadata[f"cluster_{cluster_id}"] = {
                "hdf5_file": best_db,
                "size": len(indices),
                "centroid": centroids[cluster_id].tolist(),
                "worker": assigned_worker  # ✅ Now assigns the correct worker
            }

            with h5py.File(best_db, "a") as f:
                f.create_dataset(f"embeddings_cluster_{cluster_id}", data=embeddings[indices])
                f.create_dataset(f"image_paths_cluster_{cluster_id}", data=np.array(paths, dtype="S"))

            database_free_space[best_db] -= len(indices)
        else:
            print(f"Cluster {cluster_id} could not be saved due to insufficient space.")

    cluster_metadata["database_free_space"] = database_free_space
    return cluster_metadata


def create_hdf5_database():
    print("Loading data...")
    embeddings, image_paths = load_data()

    print("Performing initial 10-Means clustering...")
    labels, centroids = perform_clustering(embeddings, NUM_CLUSTERS)

    print("Recursively splitting large clusters...")
    clusters, new_centroids = split_large_clusters(embeddings, image_paths, labels, centroids)

    print("Distributing clusters into databases...")
    cluster_metadata = distribute_clusters(clusters, embeddings, new_centroids)

    print("Saving metadata...")
    with open(OUTPUT_METADATA, "w") as f:
        json.dump(cluster_metadata, f, indent=4)

    print("Database initialization complete!")


if __name__ == "__main__":
    create_hdf5_database()



