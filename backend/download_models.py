import os
import gdown

SVD_PATH = "ml/saved_models/svd_model.pkl"
SVD_GDRIVE_ID = "1WIB-lJnrIEA4_7h8XNkmMnQ4T6xutMW0"

if not os.path.exists(SVD_PATH):
    print("Downloading SVD model from Google Drive...")
    os.makedirs("ml/saved_models", exist_ok=True)
    url = f"https://drive.google.com/uc?id={SVD_GDRIVE_ID}&confirm=t"
    gdown.download(url, SVD_PATH, quiet=False, fuzzy=True)
    print("Download complete!")
else:
    print("SVD model already exists, skipping download.")
