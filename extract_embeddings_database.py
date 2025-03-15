import os
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from tqdm import tqdm

# Load CLIP model from transformers
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Code for extracting embeddings to form database
# Path to Caltech-101 dataset
dataset_path = "./101_ObjectCategories"

# Print available categories
if os.path.exists(dataset_path):
    categories = os.listdir(dataset_path)
    print("Available categories:", categories)
else:
    print("Dataset path is incorrect!")

# Select 10 categories for testing
categories = ["airplanes", "butterfly", "camera", "elephant", "flamingo",
              "lamp", "pizza", "pyramid", "starfish", "sunflower"]

# Storage for embeddings
image_data = []

def extract_clip_embedding(img_path):
    """Extracts a 512-dimensional CLIP embedding for an image."""
    try:
        image = Image.open(img_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            embedding = model.get_image_features(**inputs).cpu().numpy().flatten()
        return embedding
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

def process_images():
    """Extracts CLIP embeddings for all images in selected categories."""
    for category in categories:
        category_path = os.path.join(dataset_path, category)
        if os.path.isdir(category_path):
            print(f"Processing category: {category}")
            for filename in tqdm(os.listdir(category_path)):
                img_path = os.path.join(category_path, filename)
                embedding = extract_clip_embedding(img_path)
                if embedding is not None:
                    image_data.append({
                        "image_path": img_path,
                        "category": category,
                        "embedding": embedding.tolist()
                    })

# Run embedding extraction
process_images()

# Convert to NumPy array
embeddings_array = np.array([item["embedding"] for item in image_data])
print("Embeddings shape:", embeddings_array.shape)  # (num_images, 512)

image_paths = [item["image_path"] for item in image_data]

# Save results
np.save("image_embeddings.npy", embeddings_array)
with open("image_paths.txt", "w") as f:
    for path in image_paths:
        f.write(path + "\n")

print("CLIP Embeddings saved!")
