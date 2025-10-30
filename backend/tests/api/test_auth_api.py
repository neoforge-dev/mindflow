"""API tests for authentication endpoints."""

import pytest

from app.auth.security import decode_access_token


class TestRegistrationEndpoint:
    """Test POST /api/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_returns_201_with_user_data(self, test_client):
        """POST /api/auth/register creates user, returns 201 with user data."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securePassword123",
                "full_name": "New User",
            },
        )

        # Returns 201 Created
        assert response.status_code == 201

        # Returns user data
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert data["plan"] == "free"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_returns_400_on_duplicate_email(self, test_client):
        """Registering existing email returns 400 error."""
        # First registration
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123456",
            },
        )

        # Second registration with same email
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123456",
            },
        )

        # Returns 400 Bad Request
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_validates_email_format(self, test_client):
        """Invalid email format returns 422 validation error."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "not-a-valid-email",
                "password": "password123456",
            },
        )

        # Returns 422 Unprocessable Entity
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_validates_password_minimum_length(self, test_client):
        """Password shorter than 12 chars returns 422 validation error (NIST 2024 standard)."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",  # Only 5 chars
            },
        )

        # Returns 422 Unprocessable Entity
        assert response.status_code == 422
        error_detail = str(response.json())
        assert "12" in error_detail or "least" in error_detail.lower()

    @pytest.mark.asyncio
    async def test_register_does_not_return_password_in_response(self, test_client):
        """Registration response doesn't include password field."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "secure@example.com",
                "password": "securePassword123",
            },
        )

        # Returns 201 Created
        assert response.status_code == 201

        # Response should not contain password or password_hash
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data


class TestLoginEndpoint:
    """Test POST /api/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_returns_200_with_access_token(self, test_client):
        """POST /api/auth/login with valid credentials returns 200 with JWT token."""
        # Create user first
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "correctPassword123",
            },
        )

        # Login with correct credentials
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "correctPassword123",
            },
        )

        # Returns 200 OK
        assert response.status_code == 200

        # Returns token
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_returns_401_on_wrong_password(self, test_client):
        """Login with wrong password returns 401 unauthorized."""
        # Create user
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "correctPassword123",
            },
        )

        # Login with wrong password
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongPassword456",
            },
        )

        # Returns 401 Unauthorized
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_returns_401_on_nonexistent_email(self, test_client):
        """Login with unknown email returns 401 unauthorized."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somePassword123",
            },
        )

        # Returns 401 Unauthorized (same as wrong password - security)
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_token_includes_user_id_in_claims(self, test_client):
        """Decoded JWT contains user_id in sub claim (no email for security)."""
        # Create user
        register_response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "tokentest@example.com",
                "password": "password123456",
            },
        )
        user_id = register_response.json()["id"]

        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "tokentest@example.com",
                "password": "password123456",
            },
        )

        # Decode token
        token = login_response.json()["access_token"]
        payload = decode_access_token(token)

        # Token contains user_id in 'sub' claim
        assert "sub" in payload
        assert payload["sub"] == user_id

        # Token should NOT contain email (security: minimal payload)
        assert "email" not in payload


class TestCurrentUserEndpoint:
    """Test GET /api/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_returns_200_with_user_data(self, test_client):
        """GET /api/auth/me with valid JWT returns 200 with user data."""
        # Create user and login
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "password123456",
                "full_name": "Current User",
            },
        )
        login_response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "currentuser@example.com",
                "password": "password123456",
            },
        )
        token = login_response.json()["access_token"]

        # Get current user info
        response = await test_client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Returns 200 OK
        assert response.status_code == 200

        # Returns user data
        data = response.json()
        assert data["email"] == "currentuser@example.com"
        assert data["full_name"] == "Current User"
        assert "id" in data

        # Should not contain password
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_returns_401_without_token(self, test_client):
        """GET /api/auth/me without Authorization header returns 401."""
        response = await test_client.get("/api/auth/me")

        # Returns 401 Unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_returns_401_with_invalid_token(self, test_client):
        """GET /api/auth/me with malformed JWT returns 401."""
        response = await test_client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
        )

        # Returns 401 Unauthorized
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test that protected endpoints require JWT authentication."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_valid_jwt(self, test_client, test_user):
        """GET /api/tasks without valid JWT returns 401."""
        # Try to access tasks without token
        response = await test_client.get("/api/tasks")

        # Returns 401 Unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_works_with_valid_jwt(self, test_client):
        """GET /api/tasks with valid JWT returns 200 with user's tasks."""
        # Create user and login
        await test_client.post(
            "/api/auth/register",
            json={
                "email": "taskuser@example.com",
                "password": "password123456",
            },
        )
        login_response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "taskuser@example.com",
                "password": "password123456",
            },
        )
        token = login_response.json()["access_token"]

        # Access tasks with valid JWT
        response = await test_client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})

        # Returns 200 OK
        assert response.status_code == 200

        # Returns tasks list (empty for new user)
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_protected_endpoint_isolates_users(self, test_client):
        """User A's JWT cannot access User B's tasks."""
        # Create user A
        await test_client.post(
            "/api/auth/register",
            json={"email": "usera@example.com", "password": "password123456"},
        )
        login_a = await test_client.post(
            "/api/auth/login",
            json={"email": "usera@example.com", "password": "password123456"},
        )
        token_a = login_a.json()["access_token"]

        # Create task for user A
        await test_client.post(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"title": "User A's task", "priority": 3},
        )

        # Create user B
        await test_client.post(
            "/api/auth/register",
            json={"email": "userb@example.com", "password": "password123456"},
        )
        login_b = await test_client.post(
            "/api/auth/login",
            json={"email": "userb@example.com", "password": "password123456"},
        )
        token_b = login_b.json()["access_token"]

        # User B should only see their own tasks (none)
        response = await test_client.get("/api/tasks", headers={"Authorization": f"Bearer {token_b}"})

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 0  # User B has no tasks
