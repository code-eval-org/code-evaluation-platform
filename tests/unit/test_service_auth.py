from services.auth.service_auth import sandbox_headers


def test_sandbox_headers_uses_explicit_token():
    headers = sandbox_headers("test-token")
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["X-Caller-Service"] == "worker"
