import shutil
import uuid

from flask import Flask, request, jsonify
import requests
from image_search_2 import search_similar_images
from insert_image import insert_image_to_database
import os
from flask_cors import CORS

# UPLOAD_FOLDER = "public/uploads/"  # Final storage for images
TEMP_IMAGE_PATH = "uploads/cropped-image.jpg"  # Source image before processing
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads/"

UPLOADS_DIR = "uploads"
PUBLIC_UPLOADS_DIR = "public/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# List of worker nodes (Modify this if you add more workers)
WORKER_NODES = {
    "worker1": "http://127.0.0.1:5001",
    "worker2": "http://127.0.0.1:5002",
    "worker3": "http://127.0.0.1:5003",
    "worker4": "http://127.0.0.1:5004",
    "worker5": "http://127.0.0.1:5005",
}

def generate_unique_filename(extension=".jpg"):
    """Generates a unique filename using UUID."""
    return str(uuid.uuid4()) + extension

@app.route('/image_search', methods=['POST'])
def image_search():
    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    image = request.files['image']
    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)  # Save image temporarily

    # Step 1: Convert to embedding and find the closest centroid
    closest_centroid, assigned_worker = search_similar_images(image_path, master_mode=True)
    print('\n\n')
    print("MASTER NODE HAS ASSIGNED ", closest_centroid, "TO: ", assigned_worker)
    print('\n\n')

    if assigned_worker not in WORKER_NODES:
        return jsonify({"error": "Worker not found for centroid"}), 500

    # Step 2: Send the search request to the assigned worker
    worker_url = WORKER_NODES[assigned_worker] + "/worker_search"
    response = requests.post(worker_url, json={"image": image_path})

    return response.json()



@app.route('/insert_images', methods=['POST'])
def insert_images():
    data = request.get_json()

    if not data or 'filenames' not in data:
        return jsonify({"error": "Missing filenames"}), 400

    filenames = data['filenames']
    print("Received filenames:", filenames)  # Debugging

    for filename in filenames:
        source_path = os.path.join(UPLOADS_DIR, filename)
        destination_path = os.path.join(PUBLIC_UPLOADS_DIR, filename)

        if os.path.exists(source_path):
            try:
                shutil.copy(source_path, destination_path)  # Copy the file
            except Exception as e:
                pass

        insert_image_to_database(destination_path, filename)

    return jsonify({"message": "Uploaded successfully!", "filenames": filenames})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
