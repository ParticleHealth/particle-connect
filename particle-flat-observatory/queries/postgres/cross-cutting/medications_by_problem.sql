-- =============================================================================
-- Query: Medications by Problem
-- Requirement: CROSS-02
-- Dialect: PostgreSQL
-- Description: Maps medications to conditions by bridging through encounters.
--              Encounters reference conditions via the comma-separated
--              condition_id_references field and practitioners via
--              practitioner_role_id_references. Medications link to practitioners
--              via practitioner_role_id. This query connects conditions to
--              medications through their shared encounter and practitioner context.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: encounters, problems, medications, practitioners
-- =============================================================================

WITH
  -- Explode comma-separated condition_id_references into individual rows
  encounter_conditions AS (
    SELECT
      "encounter_id",
      "encounter_type_name",
      TRIM(unnest(string_to_array("condition_id_references", ','))) AS condition_id,
      "patient_id"
    FROM encounters
    WHERE "condition_id_references" IS NOT NULL
      AND "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  -- Join exploded condition IDs to problems for condition details
  condition_details AS (
    SELECT
      ec."encounter_id",
      ec."encounter_type_name",
      p."condition_id",
      p."condition_name",
      p."condition_clinical_status",
      p."condition_code"
    FROM encounter_conditions ec
    INNER JOIN problems p
      ON TRIM(ec.condition_id) = TRIM(p."condition_id")
  ),

  -- Explode comma-separated practitioner_role_id_references per encounter
  encounter_practitioners AS (
    SELECT
      "encounter_id",
      TRIM(unnest(string_to_array("practitioner_role_id_references", ','))) AS practitioner_role_id
    FROM encounters
    WHERE "practitioner_role_id_references" IS NOT NULL
      AND "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  -- Medications prescribed by practitioners involved in encounters
  practitioner_medications AS (
    SELECT
      m."medication_name",
      m."medication_code",
      m."medication_statement_status",
      m."practitioner_role_id"
    FROM medications m
    WHERE m."patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND m."practitioner_role_id" IS NOT NULL
  )

-- Bridge: condition -> encounter -> practitioner -> medication
SELECT DISTINCT
  cd."condition_name",
  cd."condition_clinical_status",
  cd."condition_code",
  cd."encounter_type_name",
  pm."medication_name",
  pm."medication_statement_status",
  pm."medication_code"
FROM condition_details cd
INNER JOIN encounter_practitioners ep
  ON cd."encounter_id" = ep."encounter_id"
INNER JOIN practitioner_medications pm
  ON TRIM(ep.practitioner_role_id) = TRIM(pm."practitioner_role_id")
ORDER BY cd."condition_name", pm."medication_name";


-- =============================================================================
-- Alternative: Side-by-side view (no direct medication-to-condition linkage
-- in Particle flat data)
--
-- Particle flat data does not include a direct medication-to-condition
-- relationship. This alternative view presents all active conditions and all
-- medications for the patient side-by-side for manual correlation.
-- =============================================================================

-- WITH
--   active_conditions AS (
--     SELECT
--       "condition_name",
--       "condition_clinical_status",
--       "condition_code",
--       "condition_onset_date"
--     FROM problems
--     WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'
--       AND "condition_clinical_status" = 'active'
--     ORDER BY "condition_onset_date"
--   ),
--   current_medications AS (
--     SELECT
--       "medication_name",
--       "medication_statement_status",
--       "medication_code",
--       "medication_statement_start_time"
--     FROM medications
--     WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'
--     ORDER BY "medication_name"
--   )
-- SELECT
--   ac."condition_name",
--   ac."condition_clinical_status",
--   cm."medication_name",
--   cm."medication_statement_status"
-- FROM active_conditions ac
-- CROSS JOIN current_medications cm
-- ORDER BY ac."condition_name", cm."medication_name";
