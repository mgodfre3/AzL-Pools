"""Dataset loader for aerial pool detection training data.

Expected directory structure:
    data_dir/
        images/
            001.png
            002.png
        masks/
            001.png  (binary mask: white=pool, black=background)
            002.png
"""

import os
from pathlib import Path

import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import torch


class PoolDataset(Dataset):
    def __init__(self, data_dir: str, image_size: int = 256):
        self.image_size = image_size
        self.images_dir = Path(data_dir) / "images"
        self.masks_dir = Path(data_dir) / "masks"
        self.filenames = sorted(os.listdir(self.images_dir))

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):
        fname = self.filenames[idx]

        img = Image.open(self.images_dir / fname).convert("RGB").resize((self.image_size, self.image_size))
        mask = Image.open(self.masks_dir / fname).convert("L").resize((self.image_size, self.image_size))

        img_arr = np.array(img, dtype=np.float32) / 255.0
        mask_arr = np.array(mask, dtype=np.float32) / 255.0

        img_tensor = torch.from_numpy(img_arr).permute(2, 0, 1)  # HWC → CHW
        mask_tensor = torch.from_numpy(mask_arr).unsqueeze(0)  # HW → 1HW

        return img_tensor, mask_tensor
