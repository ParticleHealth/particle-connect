-- =============================================================================
-- Query: Medication List
-- Dialect: SQLite
-- Description: All medications for a patient with dosage, route, status,
--              and start/end dates. Ordered by most recent start date.
-- Parameters: :patient_id
-- Tables: medications
-- =============================================================================

SELECT
  "medication_name",
  "medication_code",
  "medication_code_system",
  "medication_statement_status",
  "medication_statement_start_time" AS start_date,
  "medication_statement_end_time" AS end_date,
  "medication_statement_dose_value" AS dose_value,
  "medication_statement_dose_unit" AS dose_unit,
  "medication_statement_dose_route" AS route,
  "medication_statement_patient_instructions" AS instructions,
  "medication_statement_id",
  "practitioner_role_id"
FROM medications
WHERE "_patient_id" = :patient_id
ORDER BY "medication_statement_start_time" DESC;
