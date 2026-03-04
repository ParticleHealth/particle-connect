# API Reference — Management API

The Particle Health Management API manages organizational resources: projects, service accounts, and credentials. This is a separate API from the Query Flow API, with different base URLs.

## Base URLs

| Environment | Auth URL | Management URL |
|-------------|----------|---------------|
| Sandbox | `https://sandbox.particlehealth.com` | `https://management.sandbox.particlehealth.com` |
| Production | `https://api.particlehealth.com` | `https://management.particlehealth.com` |

**Important**: Auth endpoint is on the standard base URL. Management endpoints are on a separate `management.*` subdomain.

## Authentication

```
POST /auth
Headers:
  client-id: <org-level-client-id>
  client-secret: <org-level-client-secret>

Response: URL-encoded form data or JSON with access_token and expires_in
```

Management API uses org-level credentials (not project-level). The response format differs from the Query Flow API — it may return URL-encoded form data instead of plain text JWT.

## Endpoints

### Projects

**List projects**
```
GET /v1/projects
Authorization: Bearer <token>

Response: { "projects": [...] }
```

**Create project**
```
POST /v1/projects
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
  "project": {
    "display_name": "string",
    "npi": "string (NPI number)",
    "state": "STATE_ACTIVE | STATE_INACTIVE",
    "commonwell_type": "COMMONWELL_TYPE_POSTACUTECARE",
    "address": {
      "line1": "string",
      "city": "string",
      "state": "string",
      "postal_code": "string"
    }
  }
}
```

**Get project**
```
GET /v1/projects/{project_id}
```

**Update project**
```
PATCH /v1/projects/{project_id}
Body: { fields to update }
```

### Service Accounts

**List service accounts**
```
GET /v1/serviceaccounts
```

**Create service account**
```
POST /v1/serviceaccounts
Body:
{
  "service_account": {
    "display_name": "string"
  }
}
```

**Get service account**
```
GET /v1/serviceaccounts/{account_id}
```

### IAM Policies

**Set policy** (assign roles to projects)
```
POST /v1/serviceaccounts/{account_id}:setPolicy
Body:
{
  "bindings": [
    {
      "role": "organization.owner | project.owner | project.user",
      "resources": ["projects/{project_id}"]
    }
  ]
}
```

**Get policy**
```
GET /v1/serviceaccounts/{account_id}:getPolicy
```

### Credentials

**Create credentials**
```
POST /v1/serviceaccounts/{account_id}/credentials
Body (optional):
{
  "oldCredentialTtlHours": 24
}

Response: { "clientId": "...", "clientSecret": "..." }
```

**Warning**: Client secret is returned only once. Copy immediately.

**List credentials**
```
GET /v1/serviceaccounts/{account_id}/credentials
```
Note: May not be supported in sandbox (returns 405/501).

**Delete credential**
```
DELETE /v1/serviceaccounts/{account_id}/credentials/{credential_id}
```

## IAM Roles

| Role | Management API Access | Query Flow API Access |
|------|----------------------|----------------------|
| `organization.owner` | Full access to all resources | No |
| `project.owner` | Project-scoped management | Yes |
| `project.user` | No management access | Yes |

### Notifications (Webhooks)

**List notifications**
```
GET /v1/notifications
```

**Create notification**
```
POST /v1/notifications
```

**Get/Update/Delete notification**
```
GET /v1/notifications/{notification_id}
PATCH /v1/notifications/{notification_id}
DELETE /v1/notifications/{notification_id}
```

**Signature keys** (for verifying webhook payloads)
```
POST /v1/notifications/{notification_id}/signaturekeys
GET /v1/notifications/{notification_id}/signaturekeys/{key_id}
DELETE /v1/notifications/{notification_id}/signaturekeys/{key_id}
```

## Implementation

The management-ui backend proxies these endpoints through FastAPI:
- Source: `management-ui/backend/app/services/particle_client.py` — Async HTTP client
- Routers: `management-ui/backend/app/routers/` — auth.py, projects.py, service_accounts.py, credentials.py, notifications.py
