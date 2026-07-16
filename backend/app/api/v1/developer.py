"""Developer Experience API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, UTC


router = APIRouter()


class ConfigUpdate(BaseModel):
    section: str
    key: str
    value: str


class BackupCreate(BaseModel):
    name: str
    backup_type: str = "full"
    components: Optional[list[str]] = None


class RestoreRequest(BaseModel):
    backup_id: str
    components: Optional[list[str]] = None


class PluginCreate(BaseModel):
    name: str
    version: str
    description: str
    plugin_type: str
    entry_point: str
    author: Optional[str] = ""


class PluginConfigUpdate(BaseModel):
    config: dict


_config_center = None
_plugin_api = None
_backup_manager = None
_diagnostics = None
_cli_registry = None
_sdk_docs = None
_template_registry = None
_installer = None


def _get_config_center():
    global _config_center
    if _config_center is None:
        from app.developer.config import config_center
        _config_center = config_center
    return _config_center


def _get_plugin_api():
    global _plugin_api
    if _plugin_api is None:
        from app.developer.plugins import plugin_api
        _plugin_api = plugin_api
    return _plugin_api


def _get_backup_manager():
    global _backup_manager
    if _backup_manager is None:
        from app.developer.backup import backup_manager
        _backup_manager = backup_manager
    return _backup_manager


def _get_diagnostics():
    global _diagnostics
    if _diagnostics is None:
        from app.developer.diagnostics import diagnostics
        _diagnostics = diagnostics
    return _diagnostics


def _get_cli_registry():
    global _cli_registry
    if _cli_registry is None:
        from app.developer.cli import cli_registry
        _cli_registry = cli_registry
    return _cli_registry


def _get_sdk_docs():
    global _sdk_docs
    if _sdk_docs is None:
        from app.developer.sdk import sdk_docs
        _sdk_docs = sdk_docs
    return _sdk_docs


def _get_template_registry():
    global _template_registry
    if _template_registry is None:
        from app.developer.templates import template_registry
        _template_registry = template_registry
    return _template_registry


def _get_installer():
    global _installer
    if _installer is None:
        from app.developer.installer import installer
        _installer = installer
    return _installer


@router.get("/developer/config")
async def get_configuration():
    center = _get_config_center()
    return center.export_config()


@router.get("/developer/config/{section}")
async def get_config_section(section: str):
    center = _get_config_center()
    try:
        return center.get_section(section)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Section '{section}' not found")


@router.put("/developer/config")
async def update_configuration(data: ConfigUpdate):
    center = _get_config_center()
    center.set(data.section, data.key, data.value)
    return {"status": "updated", "section": data.section, "key": data.key}


@router.post("/developer/config/validate")
async def validate_configuration():
    center = _get_config_center()
    return {"validations": center.validate()}


@router.get("/developer/plugins")
async def list_plugins(plugin_type: Optional[str] = None):
    api = _get_plugin_api()
    return api.list_plugins(plugin_type)


@router.get("/developer/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    api = _get_plugin_api()
    plugin = api.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.post("/developer/plugins")
async def register_plugin(data: PluginCreate):
    api = _get_plugin_api()
    from app.developer.plugins import PluginManifest
    manifest = PluginManifest(
        name=data.name,
        version=data.version,
        description=data.description,
        author=data.author,
        plugin_type=data.plugin_type,
        entry_point=data.entry_point,
        dependencies=[],
        config_schema={},
        min_platform_version="1.0.0",
    )
    plugin_id = api.register_plugin(manifest)
    return {"plugin_id": plugin_id, "status": "registered"}


@router.put("/developer/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    api = _get_plugin_api()
    success = api.enable_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "enabled"}


@router.put("/developer/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    api = _get_plugin_api()
    success = api.disable_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "disabled"}


@router.put("/developer/plugins/{plugin_id}/config")
async def update_plugin_config(plugin_id: str, data: PluginConfigUpdate):
    api = _get_plugin_api()
    api.update_plugin_config(plugin_id, data.config)
    return {"status": "updated"}


@router.get("/developer/templates")
async def list_templates(category: Optional[str] = None, language: Optional[str] = None):
    registry = _get_template_registry()
    return registry.list_templates(category, language)


@router.get("/developer/templates/{template_id}")
async def get_template(template_id: str):
    registry = _get_template_registry()
    template = registry.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/developer/templates/{template_id}/files")
async def get_template_files(template_id: str):
    registry = _get_template_registry()
    return registry.get_template_files(template_id)


@router.get("/developer/sdk/{language}")
async def get_sdk_docs(language: str):
    sdk = _get_sdk_docs()
    if language == "python":
        return sdk.get_python_sdk()
    elif language == "typescript":
        return sdk.get_typescript_sdk()
    elif language == "rest":
        return sdk.get_rest_api()
    else:
        raise HTTPException(status_code=400, detail="Invalid language. Use: python, typescript, rest")


@router.get("/developer/sdk/{language}/quickstart")
async def get_sdk_quickstart(language: str):
    sdk = _get_sdk_docs()
    try:
        from app.developer.sdk import SDKLanguage
        lang = SDKLanguage(language)
        return {"quickstart": sdk.get_quickstart(lang)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid language")


@router.get("/developer/cli/commands")
async def list_cli_commands():
    cli = _get_cli_registry()
    commands = cli.list_commands()
    return [{"name": c.name, "description": c.description, "category": c.category} for c in commands]


@router.get("/developer/cli/help")
async def get_cli_help(command: Optional[str] = None):
    cli = _get_cli_registry()
    return {"help": cli.get_help(command)}


@router.get("/developer/diagnostics")
async def run_diagnostics():
    diag = _get_diagnostics()
    return diag.run_all_checks()


@router.get("/developer/diagnostics/doctor")
async def run_doctor():
    from app.developer.diagnostics import run_doctor
    report = run_doctor()
    return report


@router.post("/developer/backup")
async def create_backup(data: BackupCreate):
    manager = _get_backup_manager()
    from app.developer.backup import BackupType
    try:
        backup_type = BackupType(data.backup_type)
    except ValueError:
        backup_type = BackupType.full
    manifest = manager.create_backup(data.name, backup_type, data.components)
    return manifest


@router.get("/developer/backup")
async def list_backups():
    manager = _get_backup_manager()
    return manager.list_backups()


@router.get("/developer/backup/{backup_id}")
async def get_backup(backup_id: str):
    manager = _get_backup_manager()
    backup = manager.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup


@router.post("/developer/backup/restore")
async def restore_backup(data: RestoreRequest):
    manager = _get_backup_manager()
    result = manager.restore_backup(data.backup_id, data.components)
    return result


@router.delete("/developer/backup/{backup_id}")
async def delete_backup(backup_id: str):
    manager = _get_backup_manager()
    success = manager.delete_backup(backup_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")
    return {"status": "deleted"}


@router.get("/developer/installer/prerequisites")
async def check_prerequisites():
    inst = _get_installer()
    return {"checks": inst.check_prerequisites()}


@router.get("/developer/installer/quickstart")
async def get_quickstart():
    inst = _get_installer()
    return {"quickstart": inst.get_quickstart()}


@router.get("/developer/installer/guide")
async def get_install_guide():
    inst = _get_installer()
    return {"guide": inst.get_install_guide()}


@router.get("/developer/logs")
async def get_logs(level: Optional[str] = None, limit: int = 100):
    return {
        "logs": [
            {"timestamp": "2025-01-01T00:00:00Z", "level": "info", "message": "ForgeAI started", "module": "main"},
            {"timestamp": "2025-01-01T00:00:01Z", "level": "info", "message": "Database connected", "module": "database"},
            {"timestamp": "2025-01-01T00:00:02Z", "level": "info", "message": "Cache connected", "module": "cache"},
        ]
    }
