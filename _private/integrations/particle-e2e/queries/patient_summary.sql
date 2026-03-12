-- =============================================================================
-- Query: Patient Summary
-- Dialect: SQLite
-- Description: Single-row patient overview with demographics, active
--              conditions, and current medications.
-- Parameters: :patient_id
-- Tables: patients, problems, medications
-- =============================================================================

WITH
  demographics AS (
    SELECT
      "_patient_id",
      "given_name" || ' ' || "family_name" AS full_name,
      "date_of_birth",
      "gender",
      "race",
      "marital_status",
      "address_line",
      "address_city",
      "address_state",
      "address_postal_code",
      "telephone",
      "language"
    FROM patients
    WHERE "_patient_id" = :patient_id
    LIMIT 1
  ),

  active_conditions AS (
    SELECT
      "_patient_id",
      GROUP_CONCAT("condition_name", '; ') AS conditions
    FROM problems
    WHERE "_patient_id" = :patient_id
      AND "condition_clinical_status" = 'active'
    GROUP BY "_patient_id"
  ),

  current_medications AS (
    SELECT
      "_patient_id",
      GROUP_CONCAT("medication_name", '; ') AS medications
    FROM medications
    WHERE "_patient_id" = :patient_id
      AND "medication_statement_status" IN ('active', 'completed')
    GROUP BY "_patient_id"
  )

SELECT
  d."_patient_id",
  d.full_name,
  d."date_of_birth",
  d."gender",
  d."race",
  d."marital_status",
  d."address_city" || ', ' || d."address_state" || ' ' || d."address_postal_code" AS address,
  d."telephone",
  d."language",
  COALESCE(ac.conditions, 'None documented') AS active_conditions,
  COALESCE(cm.medications, 'None documented') AS current_medications
FROM demographics d
LEFT JOIN active_conditions ac ON d."_patient_id" = ac."_patient_id"
LEFT JOIN current_medications cm ON d."_patient_id" = cm."_patient_id";
