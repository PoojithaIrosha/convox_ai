import argparse
import asyncio
from pathlib import Path

from convox_ai.settings import ModelSettings, get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="convox_ai")
    commands = parser.add_subparsers(dest="command", required=True)

    models = commands.add_parser("models", help="Download or try the configured models")
    model_actions = models.add_subparsers(dest="action", required=True)
    download = model_actions.add_parser("download", help="Fetch embedding and reranker models")
    download.add_argument("--cache-dir", help="defaults to HF_HOME or ~/.cache/huggingface")
    model_actions.add_parser("smoke", help="Call every configured model once")

    contracts = commands.add_parser("contracts", help="Kafka message schemas")
    contract_actions = contracts.add_subparsers(dest="action", required=True)
    export = contract_actions.add_parser("export", help="write contracts/*.schema.json")
    export.add_argument("--check", action="store_true", help="fail if a schema is out of date")
    export.add_argument("--folder", type=Path, default=Path("contracts"))

    args = parser.parse_args(argv)

    if args.command == "models" and args.action == "download":
        from convox_ai.models.download import download_models

        default = ModelSettings()
        download_models([default.embedding, default.reranker], args.cache_dir)
        return 0

    if args.command == "models" and args.action == "smoke":
        from convox_ai.models.smoke import run_smoke
        return 0 if asyncio.run(run_smoke(get_settings())) else 1

    if args.command == "contracts" and args.action == "export":
        from convox_ai.contracts.export import export as export_schemas

        stale =export_schemas(args.folder, check=args.check)
        for name in stale:
            print(f"out of date: {args.folder / name} (run: convox-ai contracts export)")
        return 1 if stale else 0

    parser.error("unknown command")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())