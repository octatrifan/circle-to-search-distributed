import json
import numpy as np
import h5py
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
from metadata_op import *
from extract_embeddings import extract_clip_embedding
from sklearn.cluster import KMeans

METADATA_FILE = "centroids_metadata.json"
MAX_CLUSTER_SIZE = 100


def split_and_assign_cluster(cluster_embeddings, image_paths, metadata, closest_cluster,
                             max_cluster_size=MAX_CLUSTER_SIZE):
    """Splits a cluster if it exceeds the max cluster size or if it exceeds available database space."""
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = kmeans.fit_predict(cluster_embeddings)

    original_db_file = metadata[closest_cluster]["hdf5_file"]
    new_clusters = {}
    for i in range(2):
        indices = np.where(labels == i)[0]
        new_db_file = find_database_with_max_space()

        new_cluster_id = f"cluster_{len(metadata)}"
        new_clusters[new_cluster_id] = {
            "centroid": kmeans.cluster_centers_[i].tolist(),
            "hdf5_file": new_db_file,
            "size": len(indices)
        }

        with h5py.File(new_db_file, "a") as f_new:
            if f"embeddings_{new_cluster_id}" in f_new:
                del f_new[f"embeddings_{new_cluster_id}"]
            if f"image_paths_{new_cluster_id}" in f_new:
                del f_new[f"image_paths_{new_cluster_id}"]

            f_new.create_dataset(f"embeddings_{new_cluster_id}", data=cluster_embeddings[indices])
            f_new.create_dataset(f"image_paths_{new_cluster_id}",
                                 data=np.array([image_paths[idx] for idx in indices], dtype="S"))

        # Update database free space
        metadata["database_free_space"][new_db_file] -= len(indices)

    # Update the original database free space
    metadata["database_free_space"][original_db_file] += metadata[closest_cluster]["size"]

    del metadata[closest_cluster]
    metadata.update(new_clusters)

    return metadata


def insert_image_to_database(image_path, metadata_file, max_cluster_size=MAX_CLUSTER_SIZE):
    """Insert an image into the database while handling cluster splitting and migration if needed."""

    query_embedding = extract_clip_embedding(image_path)

    closest_cluster, db_file = find_closest_centroid(query_embedding)

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    with h5py.File(db_file, "a") as f:
        cluster_embeddings = f[f"embeddings_{closest_cluster}"][:]
        image_paths = f[f"image_paths_{closest_cluster}"][:].astype(str).tolist()

        # Append new image
        cluster_embeddings = np.vstack([cluster_embeddings, query_embedding])
        image_paths.append(image_path)

        # Recalculate centroid
        new_centroid = np.mean(cluster_embeddings, axis=0)

        # Check if inserting image exceeds max database capacity or max cluster size
        db_free_space = metadata.get("database_free_space", {})
        if len(cluster_embeddings) > max_cluster_size or db_free_space[db_file] < 1:
            if db_free_space[db_file] < 1:
                print(f"Database {db_file} is full! Splitting cluster {closest_cluster}...")
            else:
                print(f"Cluster {closest_cluster} size {len(cluster_embeddings)} exceeds max size {max_cluster_size}! Splitting...")
            metadata = split_and_assign_cluster(cluster_embeddings, image_paths, metadata, closest_cluster, max_cluster_size)
            print(f"Inserted image {image_path} into new clusters")
        else:
            # Delete existing dataset before recreating with new size
            if f"embeddings_{closest_cluster}" in f:
                del f[f"embeddings_{closest_cluster}"]
            if f"image_paths_{closest_cluster}" in f:
                del f[f"image_paths_{closest_cluster}"]

            f.create_dataset(f"embeddings_{closest_cluster}", data=cluster_embeddings)
            f.create_dataset(f"image_paths_{closest_cluster}", data=np.array(image_paths, dtype="S"))
            metadata[closest_cluster]["centroid"] = new_centroid.tolist()
            metadata[closest_cluster]["size"] = len(cluster_embeddings)

            # Update database free space
            metadata["database_free_space"][db_file] -= 1
            print(f"Inserted image {image_path} into cluster {closest_cluster}")

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)

# Test the code by images from images/test folder
# For each of the image, insert it into the database
import os
# Read each image from the test folder
test_folder = "images/test"
for filename in os.listdir(test_folder):
    if filename.endswith(".jpg"):
        image_path = os.path.join(test_folder, filename)
        insert_image_to_database(image_path, METADATA_FILE, max_cluster_size=MAX_CLUSTER_SIZE)
