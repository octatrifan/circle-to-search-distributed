from flask import Flask, request, jsonify
from image_search_2 import search_similar_images
from insert_image import insert_image_to_database
import os
import requests
import shutil
import uuid
import threading
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


last_heartbeat_lock = threading.Lock()
last_heartbeat_value = time.time()

WORKER_ID = os.getenv("WORKER_ID", "workerdefault")
IS_MASTER = os.getenv("MASTER", "False").lower() == "true"
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

HEARTBEAT_INTERVAL = 5  # seconds
HEARTBEAT_TIMEOUT = 15  # seconds
LAST_ELECTION_TIME = 0
ELECTION_COOLDOWN = 30

last_heartbeat = time.time()
current_master = None  # Initially set to worker5


def generate_unique_filename(extension=".jpg"):
    """Generates a unique filename using UUID."""
    return str(uuid.uuid4()) + extension

def get_worker_num(worker_id):
    return int(worker_id.replace("worker", ""))

def send_heartbeat():
    if IS_MASTER:
        for worker, url in WORKER_NODES.items():
            try:
                requests.post(f"{url}/heartbeat",
                            json={"master": WORKER_ID, "seq": time.time_ns()},
                            timeout=2)
            except:
                continue


def check_master_heartbeat():
    global IS_MASTER, last_heartbeat_value
    while True:
        if not IS_MASTER:
            with last_heartbeat_lock:
                elapsed = time.time() - last_heartbeat_value

            if elapsed > HEARTBEAT_TIMEOUT:
                print("Master timeout detected")
                initiate_leader_election()
        time.sleep(1)  # More frequent checks with lock protection


def initiate_leader_election():
    global IS_MASTER, current_master
    # Convert worker IDs to integers for comparison
    higher_priority_workers = [
        w for w in WORKER_NODES
        if get_worker_num(w) > get_worker_num(WORKER_ID)
    ]
    responses = []
    for worker in higher_priority_workers:
        try:
            response = requests.post(f"{WORKER_NODES[worker]}/election",
                                     json={"candidate": WORKER_ID},
                                     timeout=2)  # Add timeout
            responses.append(True)
        except:
            continue

    if not responses:  # Only become master if NO responses
        IS_MASTER = True
        current_master = WORKER_ID
        broadcast_new_master()


def broadcast_new_master():
    global IS_MASTER
    IS_MASTER = True
    for worker, url in WORKER_NODES.items():
        if worker != WORKER_ID:
            try:
                requests.post(f"{url}/new_master", json={"master": WORKER_ID})
            except requests.exceptions.RequestException:
                print(f"Failed to notify {worker} about new master")


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    global last_heartbeat_value
    data = request.json
    with last_heartbeat_lock:
        if data.get('seq', 0) > last_heartbeat_value:
            last_heartbeat_value = data['seq']
    return jsonify({"status": "ack"})

@app.route('/election', methods=['POST'])
def election():
    data = request.json
    candidate = data['candidate']
    if candidate < WORKER_ID:
        initiate_leader_election()
        return jsonify({"status": "ok"}), 200
    else:
        return jsonify({"status": "rejected"}), 403


@app.route('/new_master', methods=['POST'])
def new_master():
    global current_master, IS_MASTER  # ← MISSING CRUCIAL UPDATE
    data = request.json
    new_master_id = data['master']

    # Add this critical line ↓
    IS_MASTER = (new_master_id == WORKER_ID)

    current_master = new_master_id
    print(f"New master is {current_master} (I am now {IS_MASTER})")
    return jsonify({"status": "ok"})


@app.route('/image_search', methods=['POST'])
def image_search():
    if not IS_MASTER:
        return jsonify({"error": "Not the master node"}), 403

    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    image = request.files['image']
    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)  # Save image temporarily

    closest_centroid, assigned_worker = search_similar_images(image_path, master_mode=True)
    print(f"\n\nMASTER NODE HAS ASSIGNED {closest_centroid} TO: {assigned_worker}\n\n")

    if assigned_worker not in WORKER_NODES:
        return jsonify({"error": "Worker not found for centroid"}), 500

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


@app.route('/worker_search', methods=['POST'])
def worker_search():
    data = request.json
    image_path = data.get("image", None)

    if not image_path:
        return jsonify({"error": "Missing image path"}), 400

    results = search_similar_images(image_path, WORKER_ID=WORKER_ID)
    print(f"\n\n-------- This is NODE {WORKER_ID}, MASTER={IS_MASTER} --------------")
    print(f"-------- RECEIVED {image_path} and successfully RETURNED the following results: {results}\n\n")
    return jsonify({"worker": WORKER_ID, "results": results})


if __name__ == '__main__':
    heartbeat_thread = threading.Thread(target=send_heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    master_check_thread = threading.Thread(target=check_master_heartbeat)
    master_check_thread.daemon = True
    master_check_thread.start()

    if not current_master and WORKER_ID == max(WORKER_NODES.keys()):
        initiate_leader_election()

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
