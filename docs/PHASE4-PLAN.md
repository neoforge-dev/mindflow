# Phase 4: Authentication & JWT Implementation Plan

**Status**: Ready to Execute
**Approach**: Outside-In TDD (Auth Tests → Implementation)
**Duration**: 6-7 hours
**Coverage Target**: >85%
**Created**: 2025-10-30
**Version**: 1.1 (Updated with security fixes)

---

## Overview

Build **JWT-based authentication** to replace temporary query parameter auth from Phase 3. This implements secure user registration, login, and protected API endpoints with proper password hashing and token validation.

**What We're Building**:
- User registration with password hashing (bcrypt)
- JWT token generation and validation
- Login endpoint returning access tokens
- Authentication middleware for protected routes
- Protected API endpoints (replace `?user_id=` with JWT)
- Password reset preparation (user lookup only, no email yet)
- 15-20 authentication tests

**What We're NOT Building** (yet):
- Email verification (Phase 5)
- Password reset email flow (Phase 5)
- Refresh tokens (Phase 5)
- OAuth/Social login (Phase 6)
- Rate limiting on auth endpoints (Phase 5)
- Account lockout after failed attempts (Phase 5)
- Two-factor authentication (Phase 6)

**Success Criteria**:
- All 15-20 auth tests pass
- >85% code coverage for auth layer
- Can register new user with hashed password
- Can login and receive JWT token
- Protected endpoints require valid JWT
- Invalid/expired tokens rejected with 401
- User passwords never stored in plaintext
- Multi-user isolation maintained via JWT claims

---

## Architecture Decision

### JWT Strategy

**Token Type**: Access tokens only (no refresh tokens yet)
**Algorithm**: HS256 (HMAC with SHA-256)
**Expiration**: 24 hours (configurable via env)
**Storage**: Client-side (Custom GPT context or localStorage for web UI)

**JWT Payload** (minimal, secure):
```json
{
  "sub": "user_id_uuid",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Security Rationale**:
- **Only user_id in payload**: JWTs are base64 (not encrypted), anyone can decode them
- **No email**: If email changes, tokens would have stale data
- **Minimal size**: Smaller tokens = less network overhead
- **Immutable data only**: Only include data that won't change during token lifetime
- **Fetch user data from DB**: Use user_id to get current email/name when needed

**Why This Approach**:
- Simple: No refresh token complexity yet
- Stateless: No server-side session storage needed
- Secure: HS256 with strong secret key, minimal payload exposure
- Scalable: Can add refresh tokens in Phase 5 without breaking changes

### Password Hashing

**Library**: `passlib` with `bcrypt`
**Rounds**: 12 (good balance of security vs performance)
**Salt**: Automatic per-password (bcrypt handles this)

**Why bcrypt**:
- Industry standard for password hashing
- Adaptive (can increase rounds as hardware improves)
- Built-in salt generation
- Resistant to rainbow table attacks

### Authentication Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ POST /api/auth/register
       │ {"email": "...", "password": "..."}
       ▼
┌─────────────────────┐
│  Registration       │
│  - Validate email   │
│  - Hash password    │
│  - Create user      │
└──────┬──────────────┘
       │
       │ 201 Created
       │ {"id": "...", "email": "..."}
       ▼
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ POST /api/auth/login
       │ {"email": "...", "password": "..."}
       ▼
┌─────────────────────┐
│  Login              │
│  - Find user        │
│  - Verify password  │
│  - Generate JWT     │
└──────┬──────────────┘
       │
       │ 200 OK
       │ {"access_token": "eyJ...", "token_type": "bearer"}
       ▼
┌─────────────┐
│   Client    │
│  (stores JWT)│
└──────┬──────┘
       │
       │ GET /api/tasks
       │ Authorization: Bearer eyJ...
       ▼
┌─────────────────────┐
│  Auth Middleware    │
│  - Validate JWT     │
│  - Extract user_id  │
│  - Inject into req  │
└──────┬──────────────┘
       │
       │ (user authenticated)
       ▼
┌─────────────────────┐
│  Task Endpoint      │
│  - Use user_id      │
│  - Return tasks     │
└─────────────────────┘
```

---

## File Changes

### New Files

**`app/auth/__init__.py`**
- Empty package file

**`app/auth/security.py`**
- Password hashing and verification
- JWT token creation and validation
- Security utilities

**`app/auth/schemas.py`**
- `UserRegister` - Registration request schema
- `UserLogin` - Login request schema
- `Token` - JWT token response schema
- `TokenData` - Decoded token data schema
- `UserResponse` - User data response (no password)

**`app/auth/service.py`**
- `AuthService.register_user()` - Create user with hashed password
- `AuthService.authenticate_user()` - Verify credentials
- `AuthService.get_user_by_email()` - User lookup for authentication

**`app/api/auth.py`**
- `POST /api/auth/register` - User registration endpoint
- `POST /api/auth/login` - Login endpoint
- (Optional) `GET /api/auth/me` - Get current user info

**`tests/auth/__init__.py`**
- Empty package file

**`tests/auth/test_security.py`**
- Unit tests for password hashing
- Unit tests for JWT creation/validation

**`tests/auth/test_auth_service.py`**
- Integration tests for AuthService

**`tests/api/test_auth_api.py`**
- API tests for registration endpoint
- API tests for login endpoint
- API tests for protected endpoints

### Modified Files

**`app/config.py`**
- Add `SECRET_KEY` setting (for JWT signing)
- Add `JWT_ALGORITHM` setting (default: "HS256")
- Add `ACCESS_TOKEN_EXPIRE_HOURS` setting (default: 24)

**`app/db/crud.py`**
- Add `UserCRUD` class with `create()`, `get_by_email()`, `get_by_id()` methods
- Needed for user registration and authentication

**`app/dependencies.py`**
- Add `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")`
- Update `get_current_user_id()` to validate JWT instead of query param
- Add `get_current_user()` to return full User object

**`app/api/tasks.py`**
- Update all endpoints to use JWT auth (remove `?user_id=` query params)
- Use `Depends(get_current_user_id)` without manual parameter

**`app/main.py`**
- Register auth router
- No other changes needed

**`tests/conftest.py`**
- Add `auth_headers()` fixture - Generate JWT for testing
- Add `test_user_with_password` fixture - User with known password (avoids circular dependency)

**`pyproject.toml`**
- Add `passlib[bcrypt]` dependency
- Add `python-jose[cryptography]` dependency (for JWT)

---

## Function Specifications

### `app/auth/security.py`

#### `hash_password(password: str) -> str`
Hashes a plain text password using bcrypt with 12 rounds. Returns the hashed password string suitable for database storage.

#### `verify_password(plain_password: str, hashed_password: str) -> bool`
Verifies a plain text password against a bcrypt hash. Returns True if password matches, False otherwise. Constant-time comparison prevents timing attacks.

#### `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
Creates a JWT access token with the provided payload data. Sets expiration time to `expires_delta` if provided, otherwise uses default from config. Returns encoded JWT string.

#### `decode_access_token(token: str) -> dict`
Decodes and validates a JWT access token. Raises `JWTError` if token is invalid, expired, or malformed. Returns decoded payload dictionary on success.

---

### `app/db/crud.py` (NEW: UserCRUD)

#### `UserCRUD.create(session: AsyncSession, data: dict) -> User`
Creates a new user record in database. Accepts dict with email, password_hash, full_name. Commits transaction and returns created User object with ID.

#### `UserCRUD.get_by_email(session: AsyncSession, email: str) -> User | None`
Finds user by email address. Returns User object if found, None otherwise. Case-sensitive email lookup.

#### `UserCRUD.get_by_id(session: AsyncSession, user_id: UUID) -> User | None`
Finds user by UUID primary key. Returns User object if found, None otherwise.

---

### `app/auth/service.py`

#### `AuthService.register_user(session: AsyncSession, email: str, password: str, full_name: str | None = None) -> User`
Creates a new user account with hashed password. Validates email uniqueness via UserCRUD, hashes password with bcrypt, creates user record via UserCRUD. Raises `ValueError` if email already exists. Returns created User object.

#### `AuthService.authenticate_user(session: AsyncSession, email: str, password: str) -> User | None`
Authenticates user credentials. Finds user by email via UserCRUD, verifies password hash using verify_password(). Returns User object if authentication successful, None if email not found or password incorrect (same response for security).

---

### `app/api/auth.py`

#### `register(user_data: UserRegister, db: AsyncSession = Depends(get_db)) -> UserResponse`
POST /api/auth/register endpoint. Validates registration data, creates user with hashed password via AuthService. Returns 201 with user data (no password) on success, 400 if email exists.

#### `login(credentials: UserLogin, db: AsyncSession = Depends(get_db)) -> Token`
POST /api/auth/login endpoint. Authenticates user credentials via AuthService, generates JWT access token on success. Returns 200 with token on success, 401 if credentials invalid.

#### `get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse`
GET /api/auth/me endpoint (optional). Returns current authenticated user's information. Requires valid JWT in Authorization header. Returns 200 with user data, 401 if not authenticated.

---

### `app/dependencies.py` (Updates)

**Add imports**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
```

#### `get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID`
**UPDATED**: Extracts and validates JWT from Authorization header. Decodes token using `decode_access_token()`, extracts user_id from `sub` claim. Returns user_id UUID. Raises HTTPException(401) if token invalid/expired/missing.

#### `get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User`
**NEW**: Validates JWT and retrieves full User object from database. Decodes token to get user_id, fetches user via UserCRUD.get_by_id(). Returns User object. Raises HTTPException(401) if token invalid OR if user not found (security: never reveal whether user exists from a valid JWT).

---

## Test Specifications

### `tests/auth/test_security.py` (Unit Tests)

#### `test_hash_password_generates_unique_salt_each_time()`
Same password hashed twice produces different hashes due to unique salt

#### `test_verify_password_returns_true_for_correct_password()`
Correct password verifies successfully against its hash

#### `test_verify_password_returns_false_for_wrong_password()`
Wrong password verification returns False without raising exception

#### `test_create_access_token_returns_valid_jwt()`
Generated JWT can be decoded and contains expected payload

#### `test_create_access_token_includes_expiration()`
JWT includes exp claim set to future timestamp

#### `test_decode_access_token_returns_payload()`
Valid JWT decodes successfully and returns original payload data

#### `test_decode_access_token_raises_on_expired_token()`
Expired JWT raises JWTError when decoded

#### `test_decode_access_token_raises_on_invalid_signature()`
JWT with wrong signature raises JWTError when decoded

#### `test_decode_access_token_validates_expiration_with_clock_skew()`
Token expiring during request processing handled correctly (edge case)

---

### `tests/auth/test_auth_service.py` (Integration Tests)

#### `test_register_user_creates_user_with_hashed_password()`
Registration creates user, password hashed, verifies correctly

#### `test_register_user_raises_on_duplicate_email()`
Registering same email twice raises ValueError

#### `test_authenticate_user_returns_user_on_correct_credentials()`
Valid email/password returns User object

#### `test_authenticate_user_returns_none_on_wrong_password()`
Valid email but wrong password returns None

#### `test_authenticate_user_returns_none_on_nonexistent_email()`
Email not in database returns None without raising

#### `test_get_user_by_email_returns_user_if_exists()`
Existing email returns User object

#### `test_get_user_by_email_returns_none_if_not_exists()`
Non-existent email returns None

---

### `tests/api/test_auth_api.py` (API Tests)

#### `test_register_returns_201_with_user_data()`
POST /api/auth/register creates user, returns 201 with user data

#### `test_register_returns_400_on_duplicate_email()`
Registering existing email returns 400 error

#### `test_register_validates_email_format()`
Invalid email format returns 422 validation error

#### `test_register_validates_password_minimum_length()`
Password shorter than 12 chars returns 422 validation error (NIST 2024 standard)

#### `test_register_does_not_return_password_in_response()`
Registration response doesn't include password field

#### `test_login_returns_200_with_access_token()`
POST /api/auth/login with valid credentials returns 200 with JWT token

#### `test_login_returns_401_on_wrong_password()`
Login with wrong password returns 401 unauthorized

#### `test_login_returns_401_on_nonexistent_email()`
Login with unknown email returns 401 unauthorized

#### `test_login_token_includes_user_id_in_claims()`
Decoded JWT contains user_id in sub claim

#### `test_get_current_user_returns_200_with_user_data()`
GET /api/auth/me with valid JWT returns 200 with user data

#### `test_get_current_user_returns_401_without_token()`
GET /api/auth/me without Authorization header returns 401

#### `test_get_current_user_returns_401_with_invalid_token()`
GET /api/auth/me with malformed JWT returns 401

#### `test_protected_endpoint_requires_valid_jwt()`
GET /api/tasks without valid JWT returns 401

#### `test_protected_endpoint_works_with_valid_jwt()`
GET /api/tasks with valid JWT returns 200 with user's tasks

#### `test_protected_endpoint_isolates_users()`
User A's JWT cannot access User B's tasks

---

## Implementation Order (Outside-In TDD)

### Step 1: Setup & Configuration (30 min)
1. ✅ Add dependencies to `pyproject.toml`
2. ✅ Update `app/config.py` with JWT settings
3. ✅ Add `UserCRUD` to `app/db/crud.py`
4. ✅ Install dependencies: `make install-dev`
5. ✅ Verify no breaking changes to existing tests

### Step 2: Security Utilities (45 min)
1. ✅ Create `app/auth/security.py`
2. ✅ Implement `hash_password()` and `verify_password()`
3. ✅ Create `tests/auth/test_security.py`
4. ✅ Write 8 unit tests for password hashing/verification
5. ✅ Run tests: `make test tests/auth/test_security.py`
6. ✅ Implement `create_access_token()` and `decode_access_token()`
7. ✅ Write JWT creation/validation tests
8. ✅ All security tests pass

### Step 3: Auth Schemas (20 min)
1. ✅ Create `app/auth/schemas.py`
2. ✅ Define Pydantic models: UserRegister, UserLogin, Token, TokenData, UserResponse
3. ✅ Add email validation (@email format)
4. ✅ Add password validation (min 8 chars)

### Step 4: Auth Service (1 hour)
1. ✅ Create `app/auth/service.py`
2. ✅ Create `tests/auth/test_auth_service.py`
3. ✅ Write 7 integration tests (TDD)
4. ✅ Implement `AuthService.register_user()`
5. ✅ Implement `AuthService.authenticate_user()`
6. ✅ Implement `AuthService.get_user_by_email()`
7. ✅ Run tests: `make test tests/auth/`
8. ✅ All auth service tests pass

### Step 5: Auth API Endpoints (1.5 hours)
1. ✅ Create `app/api/auth.py`
2. ✅ Create `tests/api/test_auth_api.py`
3. ✅ Write 15 API tests (TDD)
4. ✅ Implement `POST /api/auth/register`
5. ✅ Implement `POST /api/auth/login`
6. ✅ Implement `GET /api/auth/me` (optional)
7. ✅ Register auth router in `app/main.py`
8. ✅ Run tests: `make test tests/api/test_auth_api.py`
9. ✅ All auth API tests pass

### Step 6: Update Dependencies (45 min)
1. ✅ Add `oauth2_scheme` to `app/dependencies.py`
2. ✅ Implement JWT validation in `get_current_user_id()`
3. ✅ Implement `get_current_user()` (returns 401 if user not found)
4. ✅ Update test fixtures in `tests/conftest.py`
5. ✅ Add `auth_headers()` fixture
6. ✅ Add `test_user_with_password` fixture (avoids circular dependency)

### Step 7: Migrate Task Endpoints (1.5 hours)
1. ✅ Update all endpoints in `app/api/tasks.py`
2. ✅ Remove `user_id` query parameter
3. ✅ Use `Depends(get_current_user_id)` instead
4. ✅ Update ALL tests in `tests/api/test_tasks_api.py`
5. ✅ Replace `?user_id=` with JWT auth headers
6. ✅ Run full test suite: `make test`
7. ✅ All 55+ tests pass (including new auth tests)

### Step 8: Final Validation (30 min)
1. ✅ Run full test suite: `make test`
2. ✅ Verify >85% coverage
3. ✅ Run linting: `make lint`
4. ✅ Manual testing with curl/httpie
5. ✅ Test OpenAPI docs at `/docs`
6. ✅ Verify JWT flow end-to-end
7. ✅ Commit changes

---

## Time Budget (Total: 6-7 hours)

| Step | Task | Time |
|------|------|------|
| 1 | Setup & Configuration (+ UserCRUD) | 30 min |
| 2 | Security Utilities | 45 min |
| 3 | Auth Schemas | 20 min |
| 4 | Auth Service | 1 hour |
| 5 | Auth API Endpoints | 1.5 hours |
| 6 | Update Dependencies (+ oauth2_scheme) | 45 min |
| 7 | Migrate Task Endpoints | 1.5 hours |
| 8 | Final Validation | 30 min |
| **TOTAL** | | **6.5 hours** |

**Buffer**: 30 min for unexpected issues (total: 7 hours)

---

## Success Criteria Checklist

- [ ] All 15+ auth tests pass
- [ ] All 40+ existing tests still pass (55+ total)
- [ ] >85% code coverage maintained
- [ ] Can register new user via API
- [ ] Registration hashes passwords (never plaintext)
- [ ] Can login with email/password
- [ ] Login returns valid JWT token
- [ ] Protected endpoints require JWT
- [ ] Invalid/missing JWT returns 401
- [ ] Expired JWT returns 401
- [ ] JWT contains correct user_id in claims
- [ ] User isolation maintained (can't access other user's data)
- [ ] OpenAPI docs updated with auth endpoints
- [ ] No regressions in existing functionality
- [ ] Linting passes: `make lint`
- [ ] Manual testing successful

---

## Dependencies to Add

```toml
[project]
dependencies = [
    # Existing dependencies...
    "passlib[bcrypt]>=1.7.4",        # Password hashing
    "python-jose[cryptography]>=3.3.0",  # JWT handling
]
```

**Why these libraries**:
- `passlib[bcrypt]`: Industry standard for password hashing, bcrypt is recommended for passwords
- `python-jose[cryptography]`: Pure Python JWT library with good FastAPI integration

---

## Security Considerations

### Passwords
- ✅ Never store passwords in plaintext
- ✅ Use bcrypt with 12 rounds (good security/performance balance)
- ✅ Automatic salt per password (bcrypt handles this)
- ✅ No password in API responses
- ✅ Constant-time password verification (timing attack protection)
- ✅ Minimum 12 characters (NIST 2024 standard, not outdated 8 chars)
- ✅ No maximum length (allow passphrases up to 128 chars)

### JWT Tokens
- ✅ Use strong secret key (32+ random bytes, from environment)
- ✅ Include expiration time (24 hours default)
- ✅ Validate signature on every request
- ✅ Check expiration on every request
- ✅ **Minimal payload**: Only user_id in `sub` claim (no email, no PII)
- ✅ JWTs are base64 (not encrypted) - anyone can decode them
- ✅ Use HTTPS in production (prevents token interception)

### API Endpoints
- ✅ Validate all inputs with Pydantic
- ✅ Email format validation
- ✅ Password minimum length (12 chars, NIST 2024)
- ✅ Return generic "invalid credentials" message (don't reveal which field is wrong)
- ✅ HTTP 401 for all auth failures (not 403 or 404)
- ✅ No user enumeration (same response for "email not found" and "wrong password")
- ✅ Return 401 if user deleted (never reveal user existence from valid JWT)

### Future Enhancements (Phase 5)
- Rate limiting on login endpoint (prevent brute force)
- Account lockout after N failed attempts
- Password strength requirements (uppercase, numbers, symbols)
- Email verification before account activation
- Password reset via email
- Refresh tokens (extend sessions without re-login)

### Known Limitations (Phase 4)

**Token Lifecycle**:
- ⚠️ **No logout mechanism**: Tokens remain valid until 24hr expiration
- ⚠️ **Password change doesn't invalidate tokens**: Old tokens work until expiration
- ⚠️ **Can't revoke compromised tokens**: No server-side token blacklist yet

**Why these limitations**:
- Phase 4 focuses on stateless JWT authentication (no server-side session storage)
- Token blacklist requires Redis/database + adds complexity
- 24hr expiration limits exposure window

**Mitigation**:
- Short token lifetime (24hrs) limits damage window
- Phase 5 will add refresh tokens + token blacklist
- Users can change password to invalidate future logins (existing tokens expire naturally)

**Workaround for compromised tokens**:
1. User changes password
2. Wait 24 hours for old tokens to expire
3. Future: Phase 5 adds immediate revocation

---

## Migration Notes

### Breaking Changes

**Query Parameter Auth Removed**:
```python
# OLD (Phase 3)
GET /api/tasks?user_id=123e4567-e89b-12d3-a456-426614174000

# NEW (Phase 4)
GET /api/tasks
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**All endpoints now require JWT**:
- No more `?user_id=` in URL
- Must include `Authorization: Bearer <token>` header
- Tokens obtained via `/api/auth/login`

### Custom GPT Integration

**Update GPT instructions**:
1. Call `/api/auth/login` first
2. Store `access_token` in conversation context
3. Include `Authorization: Bearer {token}` in all subsequent requests
4. If 401 received, re-authenticate

**Example GPT workflow**:
```
User: "Add task: Write blog post"

GPT Internal:
1. Check if token in context
2. If no token: Call POST /api/auth/login
3. Store token
4. Call POST /api/tasks with Authorization header
5. Return success message to user
```

---

## Testing Strategy

### Unit Tests (tests/auth/test_security.py)
Focus on password hashing and JWT creation/validation in isolation. Mock nothing - these are pure functions.

### Integration Tests (tests/auth/test_auth_service.py)
Test AuthService with real database (test database). Verify user creation, authentication, database interactions.

### API Tests (tests/api/test_auth_api.py)
Test HTTP endpoints end-to-end. Use test client with database override. Verify request/response formats, status codes, error handling.

### Regression Tests (tests/api/test_tasks_api.py)
Update existing tests to use JWT auth. Ensure no functionality broken by migration.

---

## Error Handling

### Registration Errors
- 400: Email already exists
- 422: Invalid email format
- 422: Password too short
- 500: Database error

### Login Errors
- 401: Invalid credentials (generic message for security)
- 422: Missing email or password
- 500: Database error

### Protected Endpoint Errors
- 401: Missing Authorization header
- 401: Invalid token format
- 401: Expired token
- 401: Invalid signature
- 404: User not found (after token validated)

---

## Example API Usage

### Register New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'

# Response: 201 Created
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2025-10-30T12:00:00"
}
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'

# Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Access Protected Endpoint
```bash
curl http://localhost:8000/api/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response: 200 OK
[
  {
    "id": "...",
    "title": "My task",
    ...
  }
]
```

---

## Rollback Plan

If Phase 4 implementation fails:

1. Revert commits: `git reset --hard <phase3-commit>`
2. Keep `?user_id=` auth for now
3. Deploy Phase 3 version
4. Debug issues locally
5. Re-attempt Phase 4 with fixes

**Safe because**:
- Phase 3 is fully functional
- No database schema changes
- Clean separation between phases
- All changes in new files (auth/*) or isolated to dependencies

---

**Ready to execute**: Proceed with Step 1 (Setup & Configuration)
