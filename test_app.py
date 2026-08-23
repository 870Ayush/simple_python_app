"""
Unit tests for app.py (Flask demo app used in the Harness canary/rollout demo).

20 tests, split into 4 marker groups of 5 tests each so they can be sharded
across a Harness looping (repeat) strategy:

    group1 -> "/" route behaviour
    group2 -> "/healthz" probe endpoint
    group3 -> APP_VERSION environment handling
    group4 -> routing, HTTP methods and error handling

Run one shard:   pytest -m group1
Run everything:  pytest
"""

import importlib
import os

import pytest

import app as app_module


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def client():
    """Flask test client for the currently loaded app module."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def reload_app():
    """
    Reload app.py so module-level VERSION is re-evaluated from the environment.

    Yields a callable: reload_app(version) -> freshly reloaded module.
    Always restores a clean, un-patched module afterwards.
    """
    original = os.environ.get("APP_VERSION")

    def _reload(version=None):
        if version is None:
            os.environ.pop("APP_VERSION", None)
        else:
            os.environ["APP_VERSION"] = version
        return importlib.reload(app_module)

    yield _reload

    if original is None:
        os.environ.pop("APP_VERSION", None)
    else:
        os.environ["APP_VERSION"] = original
    importlib.reload(app_module)


# --------------------------------------------------------------------------- #
# GROUP 1 — "/" home route
# --------------------------------------------------------------------------- #

@pytest.mark.group1
def test_home_returns_200(client):
    """GET / responds with HTTP 200."""
    assert client.get("/").status_code == 200


@pytest.mark.group1
def test_home_contains_greeting(client):
    """GET / body contains the demo greeting text."""
    body = client.get("/").get_data(as_text=True)
    assert "Hello from Harness demo" in body


@pytest.mark.group1
def test_home_reports_current_version(client):
    """GET / body echoes whatever VERSION the module resolved to."""
    body = client.get("/").get_data(as_text=True)
    assert f"version {app_module.VERSION}" in body


@pytest.mark.group1
def test_home_is_plain_text_html_mimetype(client):
    """A bare string return renders as text/html with a utf-8 charset."""
    resp = client.get("/")
    assert resp.mimetype == "text/html"
    assert "utf-8" in resp.headers["Content-Type"].lower()


@pytest.mark.group1
def test_home_ends_with_newline(client):
    """Body ends in a newline so `curl` output stays readable in the demo."""
    assert client.get("/").get_data(as_text=True).endswith("\n")


# --------------------------------------------------------------------------- #
# GROUP 2 — "/healthz" probe endpoint
# --------------------------------------------------------------------------- #

@pytest.mark.group2
def test_healthz_returns_200(client):
    """Readiness/liveness probe returns HTTP 200."""
    assert client.get("/healthz").status_code == 200


@pytest.mark.group2
def test_healthz_returns_json_mimetype(client):
    """Returning a dict makes Flask serialise it as application/json."""
    assert client.get("/healthz").mimetype == "application/json"


@pytest.mark.group2
def test_healthz_status_is_ok(client):
    """Payload reports status == "ok"."""
    assert client.get("/healthz").get_json()["status"] == "ok"


@pytest.mark.group2
def test_healthz_payload_has_exact_keys(client):
    """Payload exposes only the status and version keys."""
    assert set(client.get("/healthz").get_json()) == {"status", "version"}


@pytest.mark.group2
def test_healthz_is_idempotent(client):
    """Repeated probe calls return identical payloads (no hidden state)."""
    first = client.get("/healthz").get_json()
    second = client.get("/healthz").get_json()
    assert first == second


# --------------------------------------------------------------------------- #
# GROUP 3 — APP_VERSION environment handling
# --------------------------------------------------------------------------- #

@pytest.mark.group3
def test_version_defaults_to_1_0(reload_app):
    """With APP_VERSION unset, VERSION falls back to "1.0"."""
    mod = reload_app(None)
    assert mod.VERSION == "1.0"


@pytest.mark.group3
def test_version_reads_env_var(reload_app):
    """APP_VERSION overrides the default at import time."""
    mod = reload_app("2.0")
    assert mod.VERSION == "2.0"


@pytest.mark.group3
def test_home_reflects_overridden_version(reload_app):
    """A rolled-out version is visible on / — the canary proof point."""
    mod = reload_app("3.1.4")
    body = mod.app.test_client().get("/").get_data(as_text=True)
    assert "version 3.1.4" in body


@pytest.mark.group3
def test_healthz_reflects_overridden_version(reload_app):
    """The probe payload reports the same overridden version."""
    mod = reload_app("3.1.4")
    assert mod.app.test_client().get("/healthz").get_json()["version"] == "3.1.4"


@pytest.mark.group3
def test_version_is_always_a_string(reload_app):
    """Numeric-looking values stay strings, so no formatting surprises."""
    mod = reload_app("42")
    assert isinstance(mod.VERSION, str) and mod.VERSION == "42"


# --------------------------------------------------------------------------- #
# GROUP 4 — routing, methods and errors
# --------------------------------------------------------------------------- #

@pytest.mark.group4
def test_expected_routes_are_registered():
    """Both demo routes exist in the URL map."""
    rules = {r.rule for r in app_module.app.url_map.iter_rules()}
    assert {"/", "/healthz"}.issubset(rules)


@pytest.mark.group4
def test_unknown_route_returns_404(client):
    """An unmapped path returns 404 rather than erroring."""
    assert client.get("/does-not-exist").status_code == 404


@pytest.mark.group4
def test_post_to_home_returns_405(client):
    """/ only accepts GET, so POST is method-not-allowed."""
    assert client.post("/").status_code == 405


@pytest.mark.group4
def test_post_to_healthz_returns_405(client):
    """/healthz only accepts GET, so POST is method-not-allowed."""
    assert client.post("/healthz").status_code == 405


@pytest.mark.group4
def test_head_request_to_home_succeeds_with_empty_body(client):
    """HEAD / is auto-supported and returns headers with no body."""
    resp = client.head("/")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == ""
