from flask import Flask, request, jsonify
from image_search import search_similar_images
from insert_image import insert_image_to_database
from metadata_op import get_database_loading_status
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)

@app.route('/image_search', methods=['POST'])
def image_search():
    data = request.json
    if 'image_path' not in data:
        return jsonify({"error": "Missing image_path parameter"}), 400

    image_path = data['image_path']
    results = search_similar_images(image_path)

    response = {
        "images": [img[0] for img in results],
        "similarity_score": [img[1] for img in results]
    }

    return jsonify(response)

@app.route('/insert_images', methods=['POST'])
def insert_images():
    data = request.json
    if 'image_paths' not in data:
        return jsonify({"error": "Missing image_paths parameter"}), 400

    image_paths = data['image_paths']
    success_list = []
    failure_list = []

    for img_path in image_paths:
        if insert_image_to_database(img_path):
            success_list.append(img_path)
        else:
            failure_list.append(img_path)

    if len(failure_list) == 0:
        response = {"message": "Successfully inserted all images."}
    else:
        response = {
            "message": "Some images could not be inserted.",
            "not_inserted": failure_list
        }

    return jsonify(response)

@app.route('/database_status', methods=['GET'])
def database_status():
    status = get_database_loading_status()
    response = {
        "database_status": status
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
