"""Plugin validation and security checks for ForgeAI Plugin Marketplace."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """Validation check severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationCheck:
    """A single validation check result."""
    name: str
    severity: ValidationSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of plugin validation."""
    passed: bool
    errors: list[ValidationCheck] = field(default_factory=list)
    warnings: list[ValidationCheck] = field(default_factory=list)
    info: list[ValidationCheck] = field(default_factory=list)


PERMISSION_DEFINITIONS: dict[str, str] = {
    "read_repositories": "Read repository data",
    "write_repositories": "Modify repository data",
    "read_memory": "Access memory system",
    "write_memory": "Modify memory system",
    "execute_workflows": "Execute workflows",
    "manage_agents": "Manage agents",
    "access_network": "Network access",
    "read_files": "Read filesystem",
    "write_files": "Write filesystem",
    "manage_plugins": "Manage other plugins",
}

REQUIRED_MANIFEST_FIELDS = [
    "id",
    "name",
    "version",
    "description",
    "author",
    "entry_point",
]

SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-0[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
)

ENTRY_POINT_PATTERN = re.compile(r"^plugins\.[a-zA-Z0-9_.]+:[a-zA-Z_][a-zA-Z0-9_]*$")

INSECURE_PERMISSIONS = {"manage_plugins", "write_files", "manage_agents", "access_network"}


class PluginValidator:
    """Validates plugin manifests, permissions, dependencies, and security."""

    def __init__(self) -> None:
        self._validation_cache: dict[str, ValidationResult] = {}

    # ------------------------------------------------------------------
    # Manifest validation
    # ------------------------------------------------------------------

    def validate_manifest(self, manifest: dict) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        for field_name in REQUIRED_MANIFEST_FIELDS:
            if field_name not in manifest:
                errors.append(ValidationCheck(
                    name=f"manifest.missing_{field_name}",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field_name}' is missing from manifest",
                ))

        if "version" in manifest:
            version_result = self.validate_version(manifest["version"])
            errors.extend(version_result.errors)
            warnings.extend(version_result.warnings)

        if "entry_point" in manifest:
            ep_result = self.validate_entry_point(manifest["entry_point"])
            errors.extend(ep_result.errors)
            warnings.extend(ep_result.warnings)

        if "permissions" in manifest:
            perm_result = self.validate_permissions(manifest["permissions"])
            errors.extend(perm_result.errors)
            warnings.extend(perm_result.warnings)

        if "dependencies" in manifest:
            dep_result = self.validate_dependencies(manifest["dependencies"])
            errors.extend(dep_result.errors)
            warnings.extend(dep_result.warnings)

        if "config_schema" in manifest:
            schema_result = self.validate_config_schema(manifest["config_schema"])
            errors.extend(schema_result.errors)
            warnings.extend(schema_result.warnings)

        if "min_platform_version" in manifest:
            info.append(ValidationCheck(
                name="manifest.platform_version",
                severity=ValidationSeverity.INFO,
                message=f"Plugin requires platform version >= {manifest['min_platform_version']}",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Permission validation
    # ------------------------------------------------------------------

    def validate_permissions(self, permissions: list[str]) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        known = set(PERMISSION_DEFINITIONS.keys())

        for perm in permissions:
            if perm not in known:
                errors.append(ValidationCheck(
                    name=f"permission.unknown_{perm}",
                    severity=ValidationSeverity.ERROR,
                    message=f"Unknown permission: {perm}",
                    details={"valid_permissions": sorted(known)},
                ))
            elif perm in INSECURE_PERMISSIONS:
                warnings.append(ValidationCheck(
                    name=f"permission.insecure_{perm}",
                    severity=ValidationSeverity.WARNING,
                    message=f"Permission '{perm}' grants elevated privileges and requires review",
                ))

        if not permissions:
            info.append(ValidationCheck(
                name="permission.none_declared",
                severity=ValidationSeverity.INFO,
                message="Plugin declares no permissions (runs in minimal sandbox)",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Dependency validation
    # ------------------------------------------------------------------

    def validate_dependencies(self, dependencies: list[str]) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        seen: set[str] = set()
        for dep in dependencies:
            if dep in seen:
                errors.append(ValidationCheck(
                    name=f"dependency.duplicate_{dep}",
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate dependency: {dep}",
                ))
            seen.add(dep)

            parts = dep.split("==")
            if len(parts) == 2:
                version = parts[1]
                if not SEMVER_PATTERN.match(version):
                    errors.append(ValidationCheck(
                        name=f"dependency.invalid_version_{dep}",
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid version for dependency '{parts[0]}': {version}",
                    ))
            elif "@" in dep and dep.count("@") == 1:
                pass  # git URL style — acceptable
            else:
                warnings.append(ValidationCheck(
                    name=f"dependency.unpinned_{dep}",
                    severity=ValidationSeverity.WARNING,
                    message=f"Dependency '{dep}' is not pinned to a specific version",
                ))

        if not dependencies:
            info.append(ValidationCheck(
                name="dependency.none",
                severity=ValidationSeverity.INFO,
                message="Plugin has no declared dependencies",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Version validation
    # ------------------------------------------------------------------

    def validate_version(self, version: str) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        if not SEMVER_PATTERN.match(version):
            errors.append(ValidationCheck(
                name="version.invalid_format",
                severity=ValidationSeverity.ERROR,
                message=f"Version '{version}' does not follow semantic versioning (semver)",
            ))
        else:
            info.append(ValidationCheck(
                name="version.valid",
                severity=ValidationSeverity.INFO,
                message=f"Version '{version}' is valid semver",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Entry point validation
    # ------------------------------------------------------------------

    def validate_entry_point(self, entry_point: str) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        if not ENTRY_POINT_PATTERN.match(entry_point):
            errors.append(ValidationCheck(
                name="entry_point.invalid_format",
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Entry point '{entry_point}' is invalid. "
                    "Expected format: 'plugins.module.path:function_name'"
                ),
            ))
        else:
            info.append(ValidationCheck(
                name="entry_point.valid",
                severity=ValidationSeverity.INFO,
                message=f"Entry point '{entry_point}' is valid",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Config schema validation
    # ------------------------------------------------------------------

    def validate_config_schema(self, schema: dict) -> ValidationResult:
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        if "type" not in schema:
            errors.append(ValidationCheck(
                name="config_schema.missing_type",
                severity=ValidationSeverity.ERROR,
                message="Config schema must specify a 'type' field",
            ))

        if schema.get("type") == "object" and "properties" not in schema:
            warnings.append(ValidationCheck(
                name="config_schema.object_without_properties",
                severity=ValidationSeverity.WARNING,
                message="Object-type config schema should define 'properties'",
            ))

        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                if not isinstance(prop_def, dict):
                    errors.append(ValidationCheck(
                        name=f"config_schema.invalid_property_{prop_name}",
                        severity=ValidationSeverity.ERROR,
                        message=f"Property '{prop_name}' definition must be a dict",
                    ))
                elif "type" not in prop_def:
                    warnings.append(ValidationCheck(
                        name=f"config_schema.property_no_type_{prop_name}",
                        severity=ValidationSeverity.WARNING,
                        message=f"Property '{prop_name}' is missing a 'type' field",
                    ))

        if not schema:
            info.append(ValidationCheck(
                name="config_schema.empty",
                severity=ValidationSeverity.INFO,
                message="Config schema is empty — plugin has no configurable options",
            ))

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings, info=info)

    # ------------------------------------------------------------------
    # Full plugin validation
    # ------------------------------------------------------------------

    def validate_plugin(self, plugin_id: str) -> ValidationResult:
        manifest = self._load_manifest(plugin_id)
        if manifest is None:
            return ValidationResult(
                passed=False,
                errors=[ValidationCheck(
                    name="plugin.manifest_not_found",
                    severity=ValidationSeverity.ERROR,
                    message=f"Could not load manifest for plugin '{plugin_id}'",
                )],
            )

        result = self.validate_manifest(manifest)
        self._validation_cache[plugin_id] = result
        return result

    # ------------------------------------------------------------------
    # Security checks
    # ------------------------------------------------------------------

    def check_security(self, plugin_id: str) -> list[ValidationCheck]:
        checks: list[ValidationCheck] = []
        manifest = self._load_manifest(plugin_id)
        if manifest is None:
            checks.append(ValidationCheck(
                name="security.manifest_missing",
                severity=ValidationSeverity.ERROR,
                message="Cannot run security checks without a manifest",
            ))
            return checks

        permissions = manifest.get("permissions", [])
        declared_set = set(permissions)
        insecure_requested = declared_set & INSECURE_PERMISSIONS
        if insecure_requested:
            checks.append(ValidationCheck(
                name="security.elevated_permissions",
                severity=ValidationSeverity.WARNING,
                message=f"Plugin requests elevated permissions: {sorted(insecure_requested)}",
                details={"elevated_permissions": sorted(insecure_requested)},
            ))

        entry = manifest.get("entry_point", "")
        if "eval" in entry or "exec" in entry:
            checks.append(ValidationCheck(
                name="security.dangerous_entry_point",
                severity=ValidationSeverity.ERROR,
                message="Entry point references potentially dangerous builtins (eval/exec)",
            ))

        if manifest.get("sandbox", {}).get("network_access", False):
            checks.append(ValidationCheck(
                name="security.network_access",
                severity=ValidationSeverity.WARNING,
                message="Plugin requests network access — verify external endpoints",
            ))

        checks.append(ValidationCheck(
            name="security.checksum",
            severity=ValidationSeverity.INFO,
            message="Package checksum should be verified before installation",
        ))

        return checks

    # ------------------------------------------------------------------
    # Compatibility checks
    # ------------------------------------------------------------------

    def check_compatibility(self, plugin_id: str) -> ValidationResult:
        manifest = self._load_manifest(plugin_id)
        errors: list[ValidationCheck] = []
        warnings: list[ValidationCheck] = []
        info: list[ValidationCheck] = []

        if manifest is None:
            return ValidationResult(
                passed=False,
                errors=[ValidationCheck(
                    name="compatibility.manifest_missing",
                    severity=ValidationSeverity.ERROR,
                    message="Cannot check compatibility without a manifest",
                )],
            )

        min_ver = manifest.get("min_platform_version")
        if min_ver:
            platform_version = self._get_platform_version()
            if platform_version and self._compare_versions(platform_version, min_ver) < 0:
                errors.append(ValidationCheck(
                    name="compatibility.platform_version",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Platform version {platform_version} is below "
                        f"required minimum {min_ver}"
                    ),
                ))
            else:
                info.append(ValidationCheck(
                    name="compatibility.platform_ok",
                    severity=ValidationSeverity.INFO,
                    message="Platform version meets minimum requirements",
                ))

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
        )

    # ------------------------------------------------------------------
    # Full report
    # ------------------------------------------------------------------

    def get_validation_report(self, plugin_id: str) -> dict:
        manifest = self._load_manifest(plugin_id)
        validation = self.validate_plugin(plugin_id)
        security = self.check_security(plugin_id)
        compatibility = self.check_compatibility(plugin_id)

        return {
            "plugin_id": plugin_id,
            "validation_passed": validation.passed,
            "security_passed": all(c.severity != ValidationSeverity.ERROR for c in security),
            "compatibility_passed": compatibility.passed,
            "errors": [c.message for c in validation.errors],
            "warnings": [c.message for c in validation.warnings],
            "info": [c.message for c in validation.info],
            "security_checks": [
                {"name": c.name, "severity": c.severity.value, "message": c.message}
                for c in security
            ],
            "compatibility": {
                "errors": [c.message for c in compatibility.errors],
                "warnings": [c.message for c in compatibility.warnings],
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_manifest(self, plugin_id: str) -> dict | None:
        """Load a plugin manifest by ID. Returns None if not found."""
        # In production this would read from the plugin registry / filesystem.
        return None

    def _get_platform_version(self) -> str | None:
        """Return the current platform version string."""
        return "1.0.0"

    @staticmethod
    def _compare_versions(a: str, b: str) -> int:
        parts_a = [int(p) for p in a.split(".")]
        parts_b = [int(p) for p in b.split(".")]
        for x, y in zip(parts_a, parts_b):
            if x < y:
                return -1
            if x > y:
                return 1
        return 0


plugin_validator = PluginValidator()
