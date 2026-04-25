"""U-Net training script for pool detection from aerial imagery.

Usage:
    python train_unet.py --data-dir ./data --epochs 50 --batch-size 16
"""

import argparse
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from dataset import PoolDataset
from unet import UNet


def train(args):
    device = torch.device("cpu")  # CPU-only training for on-prem

    dataset = PoolDataset(args.data_dir, image_size=256)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    model = UNet(n_channels=3, n_classes=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss()

    best_val_loss = float("inf")

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, masks in val_loader:
                images, masks = images.to(device), masks.to(device)
                outputs = model(images)
                val_loss += criterion(outputs, masks).item()

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        print(f"Epoch {epoch+1}/{args.epochs} — train_loss: {train_loss:.4f}, val_loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(args.output_dir, "pool_unet_best.pth"))
            print(f"  → Saved best model (val_loss: {val_loss:.4f})")

    print("Training complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train U-Net for pool detection")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to training data")
    parser.add_argument("--output-dir", type=str, default="./models", help="Model output directory")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    train(args)
