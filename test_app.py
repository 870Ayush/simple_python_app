"""
Unit tests for the Flask application.

Tests cover all routes, response formats, status codes, and version handling.
"""

import os
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def set_app_version(monkeypatch):
    """Fixture to set APP_VERSION environment variable."""
    def _set_version(version):
        monkeypatch.setenv("APP_VERSION", version)
    return _set_version


class TestHomeRoute:
    """Tests for the home route (/)."""

    def test_home_returns_200(self, client):
        """Test that home route returns 200 status code."""
        response = client.get('/')
        assert response.status_code == 200

    def test_home_contains_hello_message(self, client):
        """Test that home route contains the expected message."""
        response = client.get('/')
        assert b"Hello from Harness demo" in response.data

    def test_home_contains_version(self, client):
        """Test that home route includes version information."""
        response = client.get('/')
        # Default version is "1.0"
        assert b"version" in response.data

    def test_home_default_version(self, client):
        """Test that home route uses default version 1.0 when not set."""
        response = client.get('/')
        assert b"1.0" in response.data

    def test_home_returns_text(self, client):
        """Test that home route returns text content."""
        response = client.get('/')
        assert response.content_type.startswith('text/')


class TestHealthzRoute:
    """Tests for the healthz route (/healthz)."""

    def test_healthz_returns_200(self, client):
        """Test that healthz route returns 200 status code."""
        response = client.get('/healthz')
        assert response.status_code == 200

    def test_healthz_returns_json(self, client):
        """Test that healthz route returns JSON content."""
        response = client.get('/healthz')
        assert response.content_type == 'application/json'

    def test_healthz_contains_status(self, client):
        """Test that healthz response contains status field."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert 'status' in json_data

    def test_healthz_status_is_ok(self, client):
        """Test that healthz status is 'ok'."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert json_data['status'] == 'ok'

    def test_healthz_contains_version(self, client):
        """Test that healthz response contains version field."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert 'version' in json_data

    def test_healthz_version_matches_default(self, client):
        """Test that healthz returns default version 1.0."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert json_data['version'] == '1.0'

    def test_healthz_json_structure(self, client):
        """Test the complete JSON structure of healthz response."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert len(json_data) == 2
        assert set(json_data.keys()) == {'status', 'version'}


class TestVersionHandling:
    """Tests for APP_VERSION environment variable handling."""

    def test_custom_version_in_home(self, client, monkeypatch):
        """Test that custom APP_VERSION is reflected in home route."""
        # Set custom version
        monkeypatch.setenv("APP_VERSION", "2.5.0")

        # Need to reload the module to pick up the new env var
        import importlib
        import app as app_module
        importlib.reload(app_module)

        # Create new client with reloaded app
        app_module.app.config['TESTING'] = True
        with app_module.app.test_client() as test_client:
            response = test_client.get('/')
            assert b"2.5.0" in response.data

    def test_custom_version_in_healthz(self, client, monkeypatch):
        """Test that custom APP_VERSION is reflected in healthz route."""
        # Set custom version
        monkeypatch.setenv("APP_VERSION", "3.1.4")

        # Reload module
        import importlib
        import app as app_module
        importlib.reload(app_module)

        # Create new client
        app_module.app.config['TESTING'] = True
        with app_module.app.test_client() as test_client:
            response = test_client.get('/healthz')
            json_data = response.get_json()
            assert json_data['version'] == '3.1.4'

    def test_empty_version_string(self, client, monkeypatch):
        """Test that empty APP_VERSION string is handled."""
        monkeypatch.setenv("APP_VERSION", "")

        import importlib
        import app as app_module
        importlib.reload(app_module)

        app_module.app.config['TESTING'] = True
        with app_module.app.test_client() as test_client:
            response = test_client.get('/healthz')
            json_data = response.get_json()
            assert json_data['version'] == ''


class TestRouteNotFound:
    """Tests for non-existent routes."""

    def test_invalid_route_returns_404(self, client):
        """Test that accessing non-existent route returns 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_invalid_post_to_home(self, client):
        """Test that POST to home route returns 405 (Method Not Allowed)."""
        response = client.post('/')
        assert response.status_code == 405

    def test_invalid_post_to_healthz(self, client):
        """Test that POST to healthz route returns 405 (Method Not Allowed)."""
        response = client.post('/healthz')
        assert response.status_code == 405


class TestResponseFormats:
    """Tests for response content and formats."""

    def test_home_response_ends_with_newline(self, client):
        """Test that home route response ends with newline."""
        response = client.get('/')
        assert response.data.endswith(b'\n')

    def test_healthz_response_tuple_structure(self, client):
        """Test that healthz returns a proper tuple with status code."""
        # This tests the actual return format from the route function
        response = client.get('/healthz')
        assert response.status_code == 200
        json_data = response.get_json()
        assert isinstance(json_data, dict)
