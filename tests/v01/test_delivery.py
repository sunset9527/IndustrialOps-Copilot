from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import yaml

from api.app import app
from industrialops.config import Settings
from industrialops.migration_audit import load_migration_inventory


ROOT = Path(__file__).resolve().parents[2]


def read_project_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_release_metadata_declares_the_application_and_test_dependencies() -> None:
    metadata = tomllib.loads(read_project_file("pyproject.toml"))
    project = metadata["project"]
    assert project["name"] == "industrialops-copilot"
    assert project["version"] == "0.1.0"
    assert metadata["build-system"]["build-backend"] == "setuptools.build_meta"
    dependency_name = re.compile(r"^[\w-]+")
    assert {dependency_name.match(spec)[0].lower() for spec in project["dependencies"]} >= {
        "bcrypt", "fastapi", "passlib", "pymysql", "pypdf", "python-docx", "sqlalchemy", "uvicorn",
    }
    assert {dependency_name.match(spec)[0].lower() for spec in project["optional-dependencies"]["test"]} >= {
        "httpx", "pytest", "pyyaml",
    }


def test_environment_example_matches_runtime_settings_and_uses_placeholder_credentials() -> None:
    assert (ROOT / ".env.example").is_file()
    values = dict(
        line.split("=", maxsplit=1)
        for line in read_project_file(".env.example").splitlines()
        if line and not line.startswith("#")
    )
    assert set(values) == {
        "INDUSTRIALOPS_API_PORT",
        "INDUSTRIALOPS_FRONTEND_PORT",
        "INDUSTRIALOPS_DATABASE_URL",
        "INDUSTRIALOPS_REDIS_KEY_PREFIX",
        "INDUSTRIALOPS_REQUEST_MAX_BYTES",
    }
    settings = Settings.from_environment(values)
    assert (settings.api_port, settings.frontend_port) == (8100, 5174)
    assert settings.database_url == "mysql+pymysql://industrialops:change-me@localhost:3306/industrialops"
    assert settings.redis_key_prefix == "industrialops:"
    assert settings.request_max_bytes == Settings.from_environment({}).request_max_bytes


def test_compose_runs_only_the_industrialops_api_on_port_8100() -> None:
    assert (ROOT / "docker-compose.yml").is_file()
    compose = yaml.safe_load(read_project_file("docker-compose.yml"))
    assert compose["name"] == "industrialops"
    assert set(compose["services"]) == {"api"}
    api = compose["services"]["api"]
    assert api["container_name"] == "industrialops-api"
    assert api["build"]["dockerfile"] == "Dockerfile"
    assert api["ports"] == ["127.0.0.1:8100:8100"]
    assert not api.get("volumes")
    assert re.search(r"\bport:\s*5174\b", read_project_file("frontend/vite.config.js"))


def test_container_entrypoint_and_build_context_exclude_local_data() -> None:
    assert (ROOT / "Dockerfile").is_file()
    dockerfile = read_project_file("Dockerfile")
    command = re.search(r"^CMD\s+(\[.*\])$", dockerfile, re.MULTILINE)
    assert command is not None
    assert json.loads(command[1]) == [
        "python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8100",
    ]
    assert re.search(r"^EXPOSE 8100$", dockerfile, re.MULTILINE)
    assert (ROOT / ".dockerignore").is_file()
    patterns = [line for line in read_project_file(".dockerignore").splitlines() if line and not line.startswith("#")]
    assert patterns[0] == "**"
    assert {line for line in patterns if line.startswith("!")} == {
        "!pyproject.toml", "!README.md", "!api/", "!api/**", "!src/", "!src/**",
    }


def test_release_readme_distinguishes_api_routes_from_library_capabilities() -> None:
    assert (ROOT / "README.md").is_file()
    readme = read_project_file("README.md")
    scope, boundary = readme.split("## 当前边界", maxsplit=1)
    documented_routes = set(re.findall(r"`(?:GET|POST|PUT|PATCH|DELETE) (/[^`]+)`", scope))
    application_routes = set(app.openapi()["paths"])
    assert documented_routes == application_routes == {"/health", "/ready"}
    for unsupported_capability in ("登录", "上传", "检索的 HTTP 接口", "工业诊断决策", "工单"):
        assert unsupported_capability in boundary
    assert "设备包加载" not in boundary
    assert "local_evidence_only" in readme


def test_third_party_notices_separate_dependency_licenses_from_copied_code() -> None:
    assert (ROOT / "THIRD_PARTY_NOTICES.md").is_file()
    notices = read_project_file("THIRD_PARTY_NOTICES.md")
    assert "## 依赖许可证" in notices
    assert "## 直接迁移的外部代码" in notices


def test_migration_inventory_records_implemented_capabilities_and_paths() -> None:
    inventory = load_migration_inventory(ROOT)
    migrated = {item["id"]: item for item in inventory["migrated_capabilities"]}
    assert set(migrated) >= {
        "api_foundation", "request_safety", "identity_and_audit", "document_processing",
        "retrieval_and_evaluation", "workflow_skeleton", "frontend_shell", "api_delivery",
    }
    for item in migrated.values():
        assert item["scope"]
        assert item["industrialops_paths"]
        assert all((ROOT / path).exists() for path in item["industrialops_paths"])


def test_runtime_and_delivery_configuration_have_no_legacy_domain_references() -> None:
    forbidden = re.compile(
        r"heritage|craft|非遗|知识图谱|knowledge[_ -]?graph|graph[_ -]?agent|"
        r"networkx|pyvis|\b(?:8000|5173):(?:8000|5173)\b|(?:localhost|127\.0\.0\.1):(?:8000|5173)\b",
        re.IGNORECASE,
    )
    runtime_paths = [
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("api/**/*.py"),
        *ROOT.glob("config/*.json*"),
        *ROOT.glob("frontend/src/**/*.*"),
        ROOT / "frontend/index.html",
        ROOT / "frontend/package.json",
        ROOT / "frontend/package-lock.json",
        ROOT / "frontend/vite.config.js",
        ROOT / "pyproject.toml",
        ROOT / ".env.example",
        ROOT / "Dockerfile",
        ROOT / "docker-compose.yml",
    ]
    # This offline audit helper intentionally names the source baseline and historical inventory.
    audit_path = ROOT / "src/industrialops/migration_audit.py"
    references = [
        str(path.relative_to(ROOT))
        for path in runtime_paths
        if path != audit_path and path.is_file() and forbidden.search(path.read_text(encoding="utf-8"))
    ]
    assert references == []
