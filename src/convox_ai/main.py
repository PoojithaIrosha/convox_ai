"""The `convox-ai` command. Parts 7, 11 and 16 add more subcommands."""

import argparse
import asyncio

from convox_ai.settings import ModelSettings, get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="convox-ai")
    commands = parser.add_subparsers(dest="command", required=True)

    models = commands.add_parser("models", help="download or try the configured models")
    model_actions = models.add_subparsers(dest="action", required=True)
    download = model_actions.add_parser("download", help="fetch embedding and reranker models")
    download.add_argument("--cache-dir", help="defaults to HF_HOME or ~/.cache/huggingface")
    model_actions.add_parser("smoke", help="call every configured model once")

    args = parser.parse_args(argv)

    if args.command == "models" and args.action == "download":
        from convox_ai.models.download import download_models

        defaults = ModelSettings()  # needs no database or Kafka settings (Docker build)
        download_models([defaults.embedding, defaults.reranker], args.cache_dir)
        return 0

    if args.command == "models" and args.action == "smoke":
        from convox_ai.models.smoke import run_smoke

        return 0 if asyncio.run(run_smoke(get_settings())) else 1

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())