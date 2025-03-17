import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def extract_clip_embedding(img_path):
    """Extracts a 512-dimensional CLIP embedding for an image."""
    print("Received imgpath ", img_path)
    try:
        image = Image.open(img_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            embedding = model.get_image_features(**inputs).cpu().numpy().flatten()
        return embedding
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None
