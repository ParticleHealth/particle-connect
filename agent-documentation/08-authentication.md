# Authentication

Particle Health uses a custom JWT authentication flow (NOT standard OAuth2). There are two separate auth flows for the two APIs.

## Query Flow API Auth

**Used by**: particle-api-quickstarts (Python SDK)

```
GET https://sandbox.particlehealth.com/auth
Headers:
  client-id: <client_id>
  client-secret: <client_secret>
  scope: <scope_id>
  accept: text/plain

Response: JWT token as plain text string
```

**Key characteristics**:
- GET request (not POST) with credentials in custom headers
- Returns plain text JWT (not JSON)
- Token TTL: 1 hour
- `scope` is the scope_id (format: `projects/<project-id>`)
- Uses project-level credentials (from a service account with `project.owner` or `project.user` role)

**SDK implementation** (`particle-api-quickstarts/src/particle/core/auth.py`):
- `TokenManager`: Tracks JWT token and expiry (extracted from `exp` claim)
- `ParticleAuth`: httpx.Auth subclass — proactive refresh 10 min before expiry, auto-retry on 401
- Token refresh is transparent to calling code

**Configuration**:
```
PARTICLE_CLIENT_ID=your-client-id
PARTICLE_CLIENT_SECRET=your-client-secret
PARTICLE_SCOPE_ID=projects/your-scope-id
```

## Management API Auth

**Used by**: management-ui (FastAPI backend)

```
POST https://sandbox.particlehealth.com/auth
Headers:
  client-id: <org_client_id>
  client-secret: <org_client_secret>

Response: URL-encoded form data OR JSON
  access_token=<jwt>&expires_in=3600
```

**Key characteristics**:
- POST request (different from Query Flow's GET)
- Uses org-level credentials (not project-level)
- No `scope` header needed
- Response may be URL-encoded form data or JSON (parser handles both)
- Token TTL: 1 hour (3600 seconds)
- Auth endpoint is on the standard URL; management API calls go to `management.*` subdomain

**Implementation** (`management-ui/backend/app/services/particle_client.py`):
- `ParticleClient`: Dataclass with async httpx client
- `_TokenState`: Tracks token validity (5 min refresh buffer)
- `connect()`: Authenticates using .env credentials
- `_ensure_token()`: Auto-refreshes before each management API request
- `switch_environment()`: Recreates HTTP clients with new base URLs

**Configuration**:
```
PARTICLE_CLIENT_ID=your-org-client-id
PARTICLE_CLIENT_SECRET=your-org-client-secret
PARTICLE_ENV=sandbox
```

## Auth Flow Comparison

| Aspect | Query Flow API | Management API |
|--------|---------------|----------------|
| Method | GET /auth | POST /auth |
| Credential level | Project (service account) | Organization |
| Scope header | Required | Not used |
| Response format | Plain text JWT | URL-encoded or JSON |
| Auth URL | Same as API base URL | Same as API base URL |
| API URL | Same host | `management.*` subdomain |

## Environment URLs

| Environment | Auth URL | Query Flow API | Management API |
|-------------|----------|---------------|----------------|
| Sandbox | `https://sandbox.particlehealth.com` | Same | `https://management.sandbox.particlehealth.com` |
| Production | `https://api.particlehealth.com` | Same | `https://management.particlehealth.com` |

## Security Notes

- Never log or commit client secrets
- JWTs are held in memory only (both SDK and management-ui)
- The SDK does not verify JWT signatures — only reads `exp` for refresh timing
- Management UI passes through client secrets from credential creation (shown once, not stored)
