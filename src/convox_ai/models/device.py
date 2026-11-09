import torch


def best_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():  # Apple Silicon GPU (your Mac)
        return "mps"
    return "cpu"
