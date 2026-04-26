import os
from huggingface_hub import hf_hub_download
import shutil

SVD_PATH = "ml/saved_models/svd_model.pkl"
REPO_ID = "kiruba1509kk/cinephy-models"

if not os.path.exists(SVD_PATH):
    print("Downloading SVD model from Hugging Face...")
    os.makedirs("ml/saved_models", exist_ok=True)
    cached = hf_hub_download(repo_id=REPO_ID, filename="svd_model.pkl")
    shutil.copy(cached, SVD_PATH)
    print("Download complete!")
else:
    print("SVD model already exists, skipping download.")
