from flask import Flask, request, jsonify
from image_search_2 import search_similar_images
import os
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

WORKER_ID = os.getenv("WORKER_ID", "workerdefault")

@app.route('/worker_search', methods=['POST'])
def worker_search():
    data = request.json
    image_path = data.get("image", None)

    if not image_path:
        return jsonify({"error": "Missing image path"}), 400

    results = search_similar_images(image_path, WORKER_ID=WORKER_ID)
    print('\n\n')
    print("-------- This is NODE", WORKER_ID, '--------------')
    print("-------- RECEIVED ", image_path, "and successfully RETURNED the following results: ", results)
    print('\n\n')
    return jsonify({"worker": WORKER_ID, "results": results})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
