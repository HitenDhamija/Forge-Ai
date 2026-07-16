"""Backup and restore system."""

import os
import json
import shutil
import hashlib
import zipfile
import tempfile
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path


BACKUP_COMPONENTS = [
    "repositories",
    "organizations",
    "knowledge",
    "learning",
    "workflows",
    "configuration",
    "prompts",
]


class BackupType(Enum):
    FULL = "full"
    REPOSITORIES = "repositories"
    ORGANIZATIONS = "organizations"
    KNOWLEDGE = "knowledge"
    CONFIGURATION = "configuration"
    WORKFLOWS = "workflows"


class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupManifest:
    id: str
    name: str
    type: str
    created_at: str
    size_bytes: int
    components: list[str] = field(default_factory=list)
    checksum: str = ""


class BackupManager:
    def __init__(self, storage_path: str = "./backups"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(self.storage_path, exist_ok=True)

    def _manifest_path(self, backup_id: str) -> str:
        return os.path.join(self.storage_path, f"{backup_id}.manifest.json")

    def _archive_path(self, backup_id: str) -> str:
        return os.path.join(self.storage_path, f"{backup_id}.zip")

    def _generate_id(self, name: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = name.lower().replace(" ", "-")[:30]
        return f"backup-{slug}-{ts}"

    def _compute_checksum(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_component_dirs(self, components: list[str]) -> dict[str, str]:
        base = os.getenv("FORGEAI_DATA_DIR", "./data")
        mapping = {
            "repositories": os.path.join(base, "repositories"),
            "organizations": os.path.join(base, "organizations"),
            "knowledge": os.path.join(base, "knowledge"),
            "learning": os.path.join(base, "learning"),
            "workflows": os.path.join(base, "workflows"),
            "configuration": os.getenv("FORGEAI_CONFIG", "./config.json"),
            "prompts": os.path.join(base, "prompts"),
        }
        return {c: mapping[c] for c in components if c in mapping}

    def create_backup(
        self,
        name: str,
        backup_type: BackupType,
        components: list[str] | None = None,
    ) -> BackupManifest:
        backup_id = self._generate_id(name)

        if backup_type == BackupType.FULL:
            target_components = list(BACKUP_COMPONENTS)
        elif components:
            target_components = [c for c in components if c in BACKUP_COMPONENTS]
        else:
            type_map = {
                BackupType.REPOSITORIES: ["repositories"],
                BackupType.ORGANIZATIONS: ["organizations"],
                BackupType.KNOWLEDGE: ["knowledge"],
                BackupType.CONFIGURATION: ["configuration"],
                BackupType.WORKFLOWS: ["workflows"],
            }
            target_components = type_map.get(backup_type, ["configuration"])

        component_dirs = self._get_component_dirs(target_components)
        archive_path = self._archive_path(backup_id)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for comp_name, comp_path in component_dirs.items():
                if os.path.isfile(comp_path):
                    zf.write(comp_path, f"{comp_name}/{os.path.basename(comp_path)}")
                elif os.path.isdir(comp_path):
                    for root, _dirs, files in os.walk(comp_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(
                                comp_name,
                                os.path.relpath(file_path, comp_path),
                            )
                            zf.write(file_path, arcname)

        size_bytes = os.path.getsize(archive_path)
        checksum = self._compute_checksum(archive_path)

        manifest = BackupManifest(
            id=backup_id,
            name=name,
            type=backup_type.value,
            created_at=datetime.now(timezone.utc).isoformat(),
            size_bytes=size_bytes,
            components=target_components,
            checksum=checksum,
        )

        with open(self._manifest_path(backup_id), "w", encoding="utf-8") as f:
            json.dump(asdict(manifest), f, indent=2)

        return manifest

    def restore_backup(
        self,
        backup_id: str,
        components: list[str] | None = None,
    ) -> dict:
        manifest = self.get_backup(backup_id)
        archive_path = self._archive_path(backup_id)

        if not os.path.exists(archive_path):
            return {"success": False, "error": "Archive file not found"}

        checksum = self._compute_checksum(archive_path)
        if checksum != manifest.checksum:
            return {"success": False, "error": "Checksum mismatch - backup may be corrupted"}

        restore_components = components or manifest.components
        restored = []
        skipped = []
        errors = []

        base = os.getenv("FORGEAI_DATA_DIR", "./data")

        with zipfile.ZipFile(archive_path, "r") as zf:
            for comp_name in restore_components:
                matching = [n for n in zf.namelist() if n.startswith(comp_name + "/")]
                if not matching:
                    skipped.append(comp_name)
                    continue
                for entry in matching:
                    target = os.path.join(base, entry)
                    try:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with zf.open(entry) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        restored.append(entry)
                    except Exception as exc:
                        errors.append({"file": entry, "error": str(exc)})

        return {
            "success": len(errors) == 0,
            "restored": restored,
            "skipped": skipped,
            "errors": errors,
        }

    def list_backups(self) -> list[BackupManifest]:
        backups = []
        for fname in os.listdir(self.storage_path):
            if fname.endswith(".manifest.json"):
                path = os.path.join(self.storage_path, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    backups.append(BackupManifest(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups

    def get_backup(self, backup_id: str) -> BackupManifest:
        path = self._manifest_path(backup_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BackupManifest(**data)

    def delete_backup(self, backup_id: str) -> bool:
        manifest_path = self._manifest_path(backup_id)
        archive_path = self._archive_path(backup_id)
        deleted = False
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
            deleted = True
        if os.path.exists(archive_path):
            os.remove(archive_path)
            deleted = True
        return deleted

    def export_backup(self, backup_id: str) -> bytes:
        archive_path = self._archive_path(backup_id)
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Backup archive not found: {backup_id}")
        with open(archive_path, "rb") as f:
            return f.read()

    def import_backup(self, data: bytes) -> str:
        tmp_dir = tempfile.mkdtemp()
        tmp_zip = os.path.join(tmp_dir, "import.zip")
        try:
            with open(tmp_zip, "wb") as f:
                f.write(data)

            backup_id = f"imported-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            shutil.copy(tmp_zip, self._archive_path(backup_id))

            manifest = BackupManifest(
                id=backup_id,
                name="Imported backup",
                type="full",
                created_at=datetime.now(timezone.utc).isoformat(),
                size_bytes=len(data),
                components=list(BACKUP_COMPONENTS),
                checksum=self._compute_checksum(self._archive_path(backup_id)),
            )
            with open(self._manifest_path(backup_id), "w", encoding="utf-8") as f:
                json.dump(asdict(manifest), f, indent=2)

            return backup_id
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def validate_backup(self, backup_id: str) -> list[str]:
        issues = []
        manifest_path = self._manifest_path(backup_id)
        archive_path = self._archive_path(backup_id)

        if not os.path.exists(manifest_path):
            issues.append("Manifest file missing")
            return issues

        if not os.path.exists(archive_path):
            issues.append("Archive file missing")
            return issues

        manifest = self.get_backup(backup_id)
        actual_size = os.path.getsize(archive_path)
        if actual_size != manifest.size_bytes:
            issues.append(f"Size mismatch: manifest={manifest.size_bytes}, actual={actual_size}")

        actual_checksum = self._compute_checksum(archive_path)
        if actual_checksum != manifest.checksum:
            issues.append(f"Checksum mismatch: manifest={manifest.checksum[:16]}..., actual={actual_checksum[:16]}...")

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                bad = zf.testzip()
                if bad:
                    issues.append(f"Corrupted file in archive: {bad}")
        except zipfile.BadZipFile:
            issues.append("Archive is not a valid ZIP file")

        return issues

    def get_backup_size(self, backup_id: str) -> int:
        archive_path = self._archive_path(backup_id)
        if not os.path.exists(archive_path):
            return 0
        return os.path.getsize(archive_path)


backup_manager = BackupManager("./backups")
