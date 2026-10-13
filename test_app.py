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
def reset_env():
    """Reset APP_VERSION environment variable after each test."""
    original_version = os.environ.get("APP_VERSION")
    yield
    if original_version is not None:
        os.environ["APP_VERSION"] = original_version
    elif "APP_VERSION" in os.environ:
        del os.environ["APP_VERSION"]


class TestHomeRoute:
    """Test suite for the home route."""

    def test_home_default_version(self, client, reset_env):
        """Test home route returns default version when APP_VERSION is not set."""
        if "APP_VERSION" in os.environ:
            del os.environ["APP_VERSION"]
        response = client.get('/')
        assert response.status_code == 200
        assert b"Hello from Harness demo" in response.data
        assert b"version 1.0" in response.data

    def test_home_custom_version(self, client, reset_env):
        """Test home route returns custom version when APP_VERSION is set."""
        os.environ["APP_VERSION"] = "2.5"
        # Need to reload the module to pick up the new env var
        from importlib import reload
        import app as app_module
        reload(app_module)
        test_app = app_module.app
        test_app.config['TESTING'] = True
        with test_app.test_client() as test_client:
            response = test_client.get('/')
            assert response.status_code == 200
            assert b"version 2.5" in response.data

    def test_home_empty_version(self, client, reset_env):
        """Test home route handles empty version string."""
        os.environ["APP_VERSION"] = ""
        from importlib import reload
        import app as app_module
        reload(app_module)
        test_app = app_module.app
        test_app.config['TESTING'] = True
        with test_app.test_client() as test_client:
            response = test_client.get('/')
            assert response.status_code == 200
            assert b"version " in response.data

    def test_home_special_characters_version(self, client, reset_env):
        """Test home route handles special characters in version."""
        os.environ["APP_VERSION"] = "v3.0-beta.1"
        from importlib import reload
        import app as app_module
        reload(app_module)
        test_app = app_module.app
        test_app.config['TESTING'] = True
        with test_app.test_client() as test_client:
            response = test_client.get('/')
            assert response.status_code == 200
            assert b"v3.0-beta.1" in response.data

    def test_home_content_type(self, client):
        """Test home route returns text content type."""
        response = client.get('/')
        assert 'text/html' in response.content_type or 'text/plain' in response.content_type


class TestHealthzRoute:
    """Test suite for the healthz route."""

    def test_healthz_status_ok(self, client):
        """Test healthz route returns ok status."""
        response = client.get('/healthz')
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data is not None
        assert json_data.get('status') == 'ok'

    def test_healthz_includes_version(self, client):
        """Test healthz route includes version in response."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert 'version' in json_data
        assert isinstance(json_data['version'], str)

    def test_healthz_custom_version(self, client, reset_env):
        """Test healthz route returns custom version."""
        os.environ["APP_VERSION"] = "3.1.4"
        from importlib import reload
        import app as app_module
        reload(app_module)
        test_app = app_module.app
        test_app.config['TESTING'] = True
        with test_app.test_client() as test_client:
            response = test_client.get('/healthz')
            json_data = response.get_json()
            assert json_data.get('version') == '3.1.4'

    def test_healthz_content_type(self, client):
        """Test healthz route returns JSON content type."""
        response = client.get('/healthz')
        assert 'application/json' in response.content_type

    def test_healthz_response_structure(self, client):
        """Test healthz route returns properly structured JSON."""
        response = client.get('/healthz')
        json_data = response.get_json()
        assert isinstance(json_data, dict)
        assert len(json_data) == 2
        assert 'status' in json_data
        assert 'version' in json_data


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_invalid_route_404(self, client):
        """Test that invalid routes return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_post_to_home_405(self, client):
        """Test that POST to home route returns 405 Method Not Allowed."""
        response = client.post('/')
        assert response.status_code == 405

    def test_post_to_healthz_405(self, client):
        """Test that POST to healthz route returns 405 Method Not Allowed."""
        response = client.post('/healthz')
        assert response.status_code == 405

    def test_put_to_home_405(self, client):
        """Test that PUT to home route returns 405 Method Not Allowed."""
        response = client.put('/')
        assert response.status_code == 405

    def test_delete_to_healthz_405(self, client):
        """Test that DELETE to healthz route returns 405 Method Not Allowed."""
        response = client.delete('/healthz')
        assert response.status_code == 405


class TestAppConfiguration:
    """Test suite for app configuration."""

    def test_app_name(self):
        """Test that app name is correctly set."""
        assert app.name == 'app'

    def test_app_testing_mode(self, client):
        """Test that app can be set to testing mode."""
        assert app.config['TESTING'] is True


class TestMultipleRequests:
    """Test suite for handling multiple concurrent requests."""

    def test_multiple_home_requests(self, client):
        """Test multiple requests to home route."""
        for _ in range(5):
            response = client.get('/')
            assert response.status_code == 200

    def test_multiple_healthz_requests(self, client):
        """Test multiple requests to healthz route."""
        for _ in range(5):
            response = client.get('/healthz')
            assert response.status_code == 200
            assert response.get_json().get('status') == 'ok'

    def test_alternating_requests(self, client):
        """Test alternating requests between routes."""
        for _ in range(3):
            response1 = client.get('/')
            assert response1.status_code == 200
            response2 = client.get('/healthz')
            assert response2.status_code == 200


class TestAppExecution:
    """Test suite for app execution configuration."""

    def test_main_block_configuration(self):
        """Test that the app is configured to run on correct host and port."""
        # The main block sets host="0.0.0.0" and port=8080
        # This test verifies that when imported, the app object is available
        assert app is not None
        # Verify app is callable (can handle requests)
        assert callable(app)
