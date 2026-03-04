async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const text = await res.text()
    let message = `Request failed: ${res.status}`
    try {
      const err = JSON.parse(text)
      message = err.detail || err.message || message
    } catch {
      if (text) message = text
    }
    throw new Error(message)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

/* ---------- Auth ---------- */

export type Environment = 'sandbox' | 'production'

export interface AuthStatus {
  authenticated: boolean
  environment: Environment
}

export async function connect(): Promise<AuthStatus> {
  return request<AuthStatus>('POST', '/api/auth/connect')
}

export async function getStatus(): Promise<AuthStatus> {
  return request<AuthStatus>('GET', '/api/auth/status')
}

export async function switchEnvironment(
  environment: Environment,
): Promise<AuthStatus> {
  return request<AuthStatus>('POST', '/api/auth/switch', { environment })
}

/* ---------- Projects ---------- */

export interface ProjectAddress {
  line1: string
  city: string
  state: string
  postal_code: string
}

export interface Project {
  name: string
  display_name: string
  npi: string
  state: string
  oid?: string
  address?: ProjectAddress
  create_time?: string
  update_time?: string
  commonwell_type?: string
  epic_approval_status?: string
  npi_type?: string
}

export function projectId(project: Project): string {
  return project.name.replace('projects/', '')
}

export async function listProjects(): Promise<Project[]> {
  const data = await request<Project[] | { projects: Project[] }>('GET', '/api/projects')
  return Array.isArray(data) ? data : (data.projects ?? [])
}

export async function getProject(id: string): Promise<Project> {
  return request<Project>('GET', `/api/projects/${id}`)
}

export async function createProject(body: {
  display_name: string
  npi: string
  state: string
  commonwell_type: string
  address: ProjectAddress
}): Promise<Project> {
  return request<Project>('POST', '/api/projects', body)
}

export async function updateProjectState(
  id: string,
  state: string,
): Promise<Project> {
  return request<Project>('PATCH', `/api/projects/${id}`, { state })
}

/* ---------- Service Accounts ---------- */

export interface ServiceAccount {
  name: string
  display_name?: string
  create_time?: string
  update_time?: string
}

export function serviceAccountId(sa: ServiceAccount): string {
  return sa.name.replace('serviceaccounts/', '')
}

export async function listServiceAccounts(): Promise<ServiceAccount[]> {
  const data = await request<ServiceAccount[] | { service_accounts?: ServiceAccount[]; serviceAccounts?: ServiceAccount[] }>(
    'GET',
    '/api/service-accounts',
  )
  if (Array.isArray(data)) return data
  return data.service_accounts ?? data.serviceAccounts ?? []
}

export async function createServiceAccount(
  displayName?: string,
): Promise<ServiceAccount> {
  return request<ServiceAccount>('POST', '/api/service-accounts', {
    display_name: displayName || 'New Service Account',
  })
}

/* ---------- Policies ---------- */

export interface PolicyBinding {
  role: string
  resources: string[]
}

export interface Policy {
  bindings: PolicyBinding[]
}

export async function getPolicy(serviceAccountId: string): Promise<Policy> {
  return request<Policy>(
    'GET',
    `/api/service-accounts/${serviceAccountId}/policy`,
  )
}

export async function setPolicy(
  serviceAccountId: string,
  bindings: PolicyBinding[],
): Promise<Policy> {
  return request<Policy>(
    'POST',
    `/api/service-accounts/${serviceAccountId}/policy`,
    { bindings },
  )
}

/* ---------- Credentials ---------- */

export interface Credential {
  id: string
  created_at?: string
  status?: string
}

export interface NewCredential {
  clientId: string
  clientSecret: string
}

export async function listCredentials(
  serviceAccountId: string,
): Promise<Credential[]> {
  const data = await request<Credential[] | { credentials: Credential[] }>(
    'GET',
    `/api/service-accounts/${serviceAccountId}/credentials`,
  )
  return Array.isArray(data) ? data : (data.credentials ?? [])
}

export async function createCredential(
  serviceAccountId: string,
  oldCredentialTtlHours: number,
): Promise<NewCredential> {
  const data = await request<Record<string, string>>(
    'POST',
    `/api/service-accounts/${serviceAccountId}/credentials`,
    { oldCredentialTtlHours },
  )
  return {
    clientId: data.clientId || data.client_id || '',
    clientSecret: data.clientSecret || data.client_secret || '',
  }
}

export async function deleteCredential(
  serviceAccountId: string,
  credentialId: string,
): Promise<void> {
  return request<void>(
    'DELETE',
    `/api/service-accounts/${serviceAccountId}/credentials/${credentialId}`,
  )
}

/* ---------- Notifications (Webhook Configs) ---------- */

export interface Notification {
  name: string
  display_name: string
  notification_type: string
  callback_url: string
  active: boolean
  create_time?: string
  update_time?: string
}

export function notificationId(n: Notification): string {
  return n.name.replace('notifications/', '')
}

export async function listNotifications(): Promise<Notification[]> {
  const data = await request<
    Notification[] | { notifications: Notification[] }
  >('GET', '/api/notifications')
  return Array.isArray(data) ? data : (data.notifications ?? [])
}

export async function createNotification(body: {
  display_name: string
  notification_type: string
  callback_url: string
  active: boolean
}): Promise<Notification> {
  return request<Notification>('POST', '/api/notifications', body)
}

export async function updateNotification(
  id: string,
  body: { display_name?: string; callback_url?: string; active?: boolean },
): Promise<Notification> {
  return request<Notification>('PATCH', `/api/notifications/${id}`, body)
}

export async function deleteNotification(id: string): Promise<void> {
  return request<void>('DELETE', `/api/notifications/${id}`)
}

/* ---------- Signature Keys ---------- */

export interface SignatureKey {
  name: string
  signature_key: string
  create_time?: string
  update_time?: string
}

export async function createSignatureKey(
  notifId: string,
  signatureKey: string,
): Promise<SignatureKey> {
  return request<SignatureKey>(
    'POST',
    `/api/notifications/${notifId}/signaturekeys`,
    { signature_key: signatureKey },
  )
}

export async function deleteSignatureKey(
  notifId: string,
  keyId: string,
): Promise<void> {
  return request<void>(
    'DELETE',
    `/api/notifications/${notifId}/signaturekeys/${keyId}`,
  )
}
