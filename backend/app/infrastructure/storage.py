from __future__ import annotations

import os
import uuid
import aiofiles
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class StorageConfig:
    backend: str = "local"
    base_path: str = "./storage"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list[str] = field(
        default_factory=lambda: [
            ".txt", ".json", ".csv", ".xlsx", ".pdf",
            ".png", ".jpg", ".jpeg", ".gif", ".svg",
            ".py", ".js", ".ts", ".yaml", ".yml", ".md",
        ]
    )


@dataclass
class FileMetadata:
    id: str
    filename: str
    content_type: str
    size: int
    path: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, file_path: str, content: bytes) -> FileMetadata:
        ...

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        ...

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        ...

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        ...

    @abstractmethod
    async def list_files(self, prefix: str) -> list[FileMetadata]:
        ...

    @abstractmethod
    async def get_url(self, file_path: str) -> str:
        ...


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str, max_file_size: int, allowed_extensions: list[str]):
        self.base_path = Path(base_path)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        return self.base_path / file_path

    def _get_content_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        content_types = {
            ".txt": "text/plain",
            ".json": "application/json",
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".py": "text/x-python",
            ".js": "application/javascript",
            ".ts": "application/typescript",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".md": "text/markdown",
        }
        return content_types.get(ext, "application/octet-stream")

    def _validate_file(self, file_path: str, content: bytes) -> None:
        if len(content) > self.max_file_size:
            raise ValueError(f"File size {len(content)} exceeds max {self.max_file_size}")
        ext = Path(file_path).suffix.lower()
        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise ValueError(f"Extension '{ext}' not allowed")

    async def upload(self, file_path: str, content: bytes) -> FileMetadata:
        self._validate_file(file_path, content)
        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        file_id = str(uuid.uuid4())
        stat = full_path.stat()
        return FileMetadata(
            id=file_id,
            filename=Path(file_path).name,
            content_type=self._get_content_type(file_path),
            size=stat.st_size,
            path=file_path,
            created_at=datetime.fromtimestamp(stat.st_ctime),
        )

    async def download(self, file_path: str) -> bytes:
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, file_path: str) -> bool:
        full_path = self._get_full_path(file_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, file_path: str) -> bool:
        return self._get_full_path(file_path).exists()

    async def list_files(self, prefix: str) -> list[FileMetadata]:
        results: list[FileMetadata] = []
        search_path = self._get_full_path(prefix) if prefix else self.base_path
        if not search_path.exists():
            return results
        for path in search_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(self.base_path)
                stat = path.stat()
                results.append(
                    FileMetadata(
                        id=str(uuid.uuid4()),
                        filename=path.name,
                        content_type=self._get_content_type(path.name),
                        size=stat.st_size,
                        path=str(rel),
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                    )
                )
        return results

    async def get_url(self, file_path: str) -> str:
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return f"file://{full_path.resolve()}"


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, region: str = "us-east-1", **kwargs: Any):
        self.bucket = bucket
        self.region = region
        self._kwargs = kwargs

    async def upload(self, file_path: str, content: bytes) -> FileMetadata:
        raise NotImplementedError("S3 support is planned for a future release")

    async def download(self, file_path: str) -> bytes:
        raise NotImplementedError("S3 support is planned for a future release")

    async def delete(self, file_path: str) -> bool:
        raise NotImplementedError("S3 support is planned for a future release")

    async def exists(self, file_path: str) -> bool:
        raise NotImplementedError("S3 support is planned for a future release")

    async def list_files(self, prefix: str) -> list[FileMetadata]:
        raise NotImplementedError("S3 support is planned for a future release")

    async def get_url(self, file_path: str) -> str:
        raise NotImplementedError("S3 support is planned for a future release")


class StorageService:
    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self._backend: StorageBackend | None = None

    def _create_backend(self) -> StorageBackend:
        if self.config.backend == "local":
            return LocalStorage(
                base_path=self.config.base_path,
                max_file_size=self.config.max_file_size,
                allowed_extensions=self.config.allowed_extensions,
            )
        elif self.config.backend == "s3":
            return S3Storage(bucket=self.config.base_path)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")

    async def upload(
        self,
        file_path: str,
        content: bytes,
        metadata: dict[str, Any] | None = None,
    ) -> FileMetadata:
        backend = self.get_backend()
        result = await backend.upload(file_path, content)
        if metadata:
            result.metadata.update(metadata)
        return result

    async def download(self, file_path: str) -> bytes:
        backend = self.get_backend()
        return await backend.download(file_path)

    async def delete(self, file_path: str) -> bool:
        backend = self.get_backend()
        return await backend.delete(file_path)

    async def get_url(self, file_path: str) -> str:
        backend = self.get_backend()
        return await backend.get_url(file_path)

    async def list_files(self, prefix: str = "") -> list[FileMetadata]:
        backend = self.get_backend()
        return await backend.list_files(prefix)

    def get_backend(self) -> StorageBackend:
        if self._backend is None:
            self._backend = self._create_backend()
        return self._backend


storage_config = StorageConfig(backend="local", base_path="./storage")
storage_service = StorageService(storage_config)
