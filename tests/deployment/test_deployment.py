"""Vérifie les artefacts de déploiement : Docker, compose, CI et Pages."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dockerfile_is_frozen_and_drops_privileges() -> None:
    dockerfile = _read("Dockerfile")
    entrypoint = _read("docker/entrypoint.sh")

    assert "uv sync --frozen --no-dev" in dockerfile
    assert 'ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]' in dockerfile
    assert 'CMD ["make", "all"]' in dockerfile
    assert "COPY . ." not in dockerfile
    assert "BEGES_DB_PATH=/app/data/warehouse/beges.duckdb" in dockerfile
    assert "HOME=/home/app" in dockerfile
    assert "exec setpriv --reuid=1000 --regid=1000 --init-groups" in entrypoint


def test_dockerignore_excludes_local_state() -> None:
    ignored = {
        line.strip().rstrip("/")
        for line in _read(".dockerignore").splitlines()
        if line.strip() and not line.startswith("#")
    }

    assert {".git", ".venv", "data", "site", "tmp", "tests"} <= ignored


def test_compose_defines_pipeline_and_web() -> None:
    compose = yaml.safe_load(_read("docker-compose.yml"))
    services = compose["services"]

    assert {"pipeline", "web"} <= set(services)
    assert services["pipeline"]["build"]["context"] == "."
    assert "8080:80" in services["web"]["ports"]
    assert services["web"]["depends_on"]["pipeline"]["condition"] == (
        "service_completed_successfully"
    )
    assert any(
        volume.startswith("beges-site:") for volume in services["web"]["volumes"]
    )
    assert {"beges-data", "beges-site"} <= set(compose["volumes"])


def test_ci_workflow_has_required_jobs() -> None:
    workflow_text = _read(".github/workflows/ci.yml")
    workflow = yaml.safe_load(workflow_text)

    assert workflow["permissions"]["contents"] == "read"
    assert {"lint-test", "pipeline", "docker", "deploy"} <= set(workflow["jobs"])
    assert workflow["jobs"]["pipeline"]["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["deploy"]["permissions"]["pages"] == "write"
    assert workflow["jobs"]["deploy"]["permissions"]["id-token"] == "write"
    assert "actions/deploy-pages@v4" in workflow_text
    assert "configure-pages" not in workflow_text
    assert "pull_request:" in workflow_text
    assert "make all" in workflow_text


def test_readme_documents_docker_and_pages() -> None:
    readme = _read("README.md")

    assert "docker compose up --build" in readme
    assert "ultragenix.github.io/Pipeline-BEGES" in readme
    assert "docs/docker-ci.md" in readme
