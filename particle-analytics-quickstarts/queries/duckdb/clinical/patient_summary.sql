-- =============================================================================
-- Query: Patient Summary
-- Requirement: CLIN-01
-- Dialect: PostgreSQL
-- Description: Returns a single-row patient summary with demographics, active
--              conditions (comma-separated), and current medications. Useful as
--              a "patient at a glance" view.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: patients, problems, medications
-- =============================================================================

WITH
  demographics AS (
    SELECT
      "patient_id",
      "given_name" || ' ' || "family_name" AS full_name,
      "date_of_birth",
      "gender",
      "race",
      "marital_status",
      "address_line",
      "address_city",
      "address_state",
      "address_postal_code",
      "address_county",
      "telephone",
      "language"
    FROM patients
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  active_conditions AS (
    SELECT
      "patient_id",
      string_agg("condition_name", '; ' ORDER BY "condition_onset_date") AS conditions
    FROM problems
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND "condition_clinical_status" = 'active'
    GROUP BY "patient_id"
  ),

  current_medications AS (
    SELECT
      "patient_id",
      string_agg("medication_name", '; ' ORDER BY "medication_name") AS medications
    FROM medications
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND "medication_statement_status" IN ('active', 'completed')
    GROUP BY "patient_id"
  )

SELECT
  d."patient_id",
  d.full_name,
  d."date_of_birth",
  d."gender",
  d."race",
  d."marital_status",
  d."address_line",
  d."address_city",
  d."address_state",
  d."address_postal_code",
  d."address_county",
  d."telephone",
  d."language",
  COALESCE(ac.conditions, 'None documented') AS active_conditions,
  COALESCE(cm.medications, 'None documented') AS current_medications
FROM demographics d
LEFT JOIN active_conditions ac ON d."patient_id" = ac."patient_id"
LEFT JOIN current_medications cm ON d."patient_id" = cm."patient_id";
