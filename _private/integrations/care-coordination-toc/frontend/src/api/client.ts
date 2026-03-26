const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body}`)
  }
  return res.json()
}

// --- Types ---

export interface Workflow {
  id: string
  patient_id: string
  patient_name: string
  status: string
  current_step: string
  created_at: string
  updated_at: string
  error_message?: string
  patient_demographics_json?: string
}

export interface WorkflowDetail extends Workflow {
  patient_context?: PatientContext | null
  call_result?: CallResult | null
  email_record?: EmailRecord | null
  gate_decisions: GateDecision[]
  events: WorkflowEvent[]
}

export interface PatientContext {
  workflow_id: string
  context: Record<string, unknown>
  care_gaps: CareGap[]
  created_at: string
}

export interface CareGap {
  type: string
  severity: string
  detail: string
}

export interface CallResult {
  workflow_id: string
  call_id?: string
  status: string
  duration_ms?: number
  transcript?: string
  disposition_action?: string
  disposition_params?: Record<string, unknown>
  created_at: string
}

export interface EmailRecord {
  workflow_id: string
  recipient_email?: string
  subject?: string
  body_html?: string
  body_text?: string
  status: string
  created_at: string
}

export interface GateDecision {
  gate_number: number
  status: string
  decision?: string
  coordinator_notes?: string
  decided_by?: string
  decided_at?: string
}

export interface WorkflowEvent {
  id: number
  workflow_id: string
  event_type: string
  event_data?: Record<string, unknown>
  created_at: string
}

export interface Patient {
  patient_id: string
  name: string
  date_of_birth: string
  gender: string
  city: string
  state: string
  active_workflows: number
}

// --- API calls ---

export const listWorkflows = (status?: string) =>
  request<Workflow[]>(`/workflows${status ? `?status=${status}` : ''}`)

export const getWorkflow = (id: string) =>
  request<WorkflowDetail>(`/workflows/${id}`)

export const createWorkflow = (data: Record<string, string>) =>
  request<Workflow>('/workflows', { method: 'POST', body: JSON.stringify(data) })

export const startWorkflow = (id: string) =>
  request<{ id: string; status: string }>(`/workflows/${id}/start`, { method: 'POST' })

export const cancelWorkflow = (id: string) =>
  request<{ id: string; status: string }>(`/workflows/${id}/cancel`, { method: 'POST' })

export const retryWorkflow = (id: string) =>
  request<{ id: string; status: string }>(`/workflows/${id}/retry`, { method: 'POST' })

export const listGates = (workflowId: string) =>
  request<GateDecision[]>(`/workflows/${workflowId}/gates`)

export const decideGate = (workflowId: string, gateNumber: number, decision: string, notes: string) =>
  request<{ gate_number: number; decision: string; workflow_status: string }>(
    `/workflows/${workflowId}/gates/${gateNumber}/decide`,
    { method: 'POST', body: JSON.stringify({ decision, coordinator_notes: notes, decided_by: 'coordinator' }) },
  )

export const listPatients = () =>
  request<Patient[]>('/patients')

export const getHealth = () =>
  request<{ status: string; db_connected: boolean }>('/health')
