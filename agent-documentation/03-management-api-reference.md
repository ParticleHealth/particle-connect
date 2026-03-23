# API Reference — Management API

The Particle Health Management API manages organizational resources: projects, service accounts, and credentials. This is a separate API from the Query Flow API, with different base URLs.

## Base URLs

| Environment | Auth URL | Management URL |
|-------------|----------|---------------|
| Sandbox | `https://sandbox.particlehealth.com` | `https://management.sandbox.particlehealth.com` |
| Production | `https://api.particlehealth.com` | `https://management.particlehealth.com` |

**Important**: Auth endpoint is on the standard base URL. Management endpoints are on a separate `management.*` subdomain.

## Authentication

```http
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
```http
GET /v1/projects
Authorization: Bearer <token>

Response: { "projects": [...] }
```

**Create project**
```http
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
```http
GET /v1/projects/{project_id}
```

**Update project**
```http
PATCH /v1/projects/{project_id}
Body: { fields to update }
```

### Service Accounts

**List service accounts**
```http
GET /v1/serviceaccounts
```

**Create service account**
```http
POST /v1/serviceaccounts
Body:
{
  "service_account": {
    "display_name": "string"
  }
}
```

**Get service account**
```http
GET /v1/serviceaccounts/{account_id}
```

### IAM Policies

**Set policy** (assign roles to projects)
```http
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
```http
GET /v1/serviceaccounts/{account_id}:getPolicy
```

### Credentials

**Create credentials**
```http
POST /v1/serviceaccounts/{account_id}/credentials
Body (optional):
{
  "oldCredentialTtlHours": 24
}

Response: { "clientId": "...", "clientSecret": "..." }
```

**Warning**: Client secret is returned only once. Copy immediately.

**List credentials**
```http
GET /v1/serviceaccounts/{account_id}/credentials
```
Note: May not be supported in sandbox (returns 405/501).

**Delete credential**
```http
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
```http
GET /v1/notifications

Response: { "notifications": [...] }
```

**Create notification**
```http
POST /v1/notifications
Body:
{
  "notification": {
    "display_name": "string",
    "notification_type": "query | patient | networkalert | hl7v2",
    "callback_url": "https://your-endpoint.example.com/webhook",
    "active": true
  }
}
```

**Get notification**
```http
GET /v1/notifications/{notification_id}
```

**Update notification**
```http
PATCH /v1/notifications/{notification_id}
Body: { "display_name": "...", "callback_url": "...", "active": true|false }
```

**Delete notification**
```http
DELETE /v1/notifications/{notification_id}
```

**Create signature key** (for verifying webhook payloads)
```http
POST /v1/notifications/{notification_id}/signaturekeys
Body:
{
  "signature_key": "string (24-80 characters)"
}

Response: { "name": "...", "signature_key": "...", "create_time": "..." }
```

**Get/Delete signature key**
```http
GET /v1/notifications/{notification_id}/signaturekeys/{key_id}
DELETE /v1/notifications/{notification_id}/signaturekeys/{key_id}
```

## Implementation

The management-ui backend proxies these endpoints through FastAPI:
- Source: `management-ui/backend/app/services/particle_client.py` — Async HTTP client
- Routers: `management-ui/backend/app/routers/` — auth.py, projects.py, service_accounts.py, credentials.py, notifications.py
