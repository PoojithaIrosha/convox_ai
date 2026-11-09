from huggingface_hub import snapshot_download

# Only the PyTorch weights, tokenizer and config are needed. bge-m3 also ships ONNX
# copies that double the download, so skip those and other formats.
_SKIP = ["onnx/*", "*.onnx", "openvino/*", "*.msgpack", "*.h5", "*.ot", "imgs/*"]


def download_models(model_ids: list[str], cache_dir: str | None = None) -> None:
    for model_id in model_ids:
        print(f"downloading {model_id} ...", flush=True)
        path = snapshot_download(model_id, cache_dir=cache_dir, ignore_patterns=_SKIP)
        print(f"  done: {path}", flush=True)