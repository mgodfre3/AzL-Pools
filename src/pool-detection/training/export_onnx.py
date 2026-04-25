"""Export trained U-Net model to ONNX format for CPU inference.

Usage:
    python export_onnx.py --model pool_unet_best.pth --output pool_detector.onnx
"""

import argparse
import torch
from unet import UNet


def export(model_path: str, output_path: str):
    model = UNet(n_channels=3, n_classes=1)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, 3, 256, 256)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["image"],
        output_names=["mask"],
        dynamic_axes={"image": {0: "batch"}, "mask": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported ONNX model to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to .pth model")
    parser.add_argument("--output", default="pool_detector.onnx", help="Output ONNX path")
    args = parser.parse_args()
    export(args.model, args.output)
