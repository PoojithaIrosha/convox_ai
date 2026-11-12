from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from convox_ai.settings import Settings
from convox_ai.shared.errors import PermanentError, RetryableError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

_NOT_FOUND = {"404", "NoSuchKey", "NotFound"}


class ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._client: S3Client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            config=Config(
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=5,
                read_timeout=60,
            ),
        )

    async def download(self, key: str, folder: Path, max_bytes: int) -> Path:
        """Save the object to folder/upload and return its path."""
        return await anyio.to_thread.run_sync(self._download, key, folder, max_bytes)

    def _download(self, key: str, folder: Path, max_bytes: int) -> Path:
        path = folder / "upload"
        try:
            size = self._client.head_object(Bucket=self._bucket, Key=key)["ContentLength"]
            if size > max_bytes:
                raise PermanentError("too_large", f"{size} bytes is over the {max_bytes} limit")
            self._client.download_file(self._bucket, key, str(path))
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in _NOT_FOUND:
                raise PermanentError("file_missing", f"no object at {key}") from e
            raise RetryableError(f"object storage error: {e}") from e
        except BotoCoreError as e:  # connection refused, timeouts
            raise RetryableError(f"object storage unreachable: {e}") from e
        return path