-- =============================================================================
-- Query: Encounter History
-- Requirement: CLIN-06
-- Dialect: PostgreSQL
-- Description: Returns all encounters for a patient in chronological order with
--              type, time range, and duration. Note that some encounters may
--              have NULL start/end times (e.g., encounter 2bcc07b5f4ebf469...).
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: encounters
-- =============================================================================

SELECT
  "encounter_id",
  "encounter_type_name",
  "encounter_type_code",
  CAST("encounter_start_time" AS TIMESTAMPTZ) AS start_time,
  CAST("encounter_end_time" AS TIMESTAMPTZ) AS end_time,
  CASE
    WHEN "encounter_start_time" IS NOT NULL
     AND "encounter_end_time" IS NOT NULL
    THEN AGE(
      CAST("encounter_end_time" AS TIMESTAMPTZ),
      CAST("encounter_start_time" AS TIMESTAMPTZ)
    )
    ELSE NULL
  END AS duration,
  "encounter_text",
  "hospitalization_discharge_disposition",
  "condition_id_references",
  "practitioner_role_id_references",
  "location_id_references"
FROM encounters
WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
ORDER BY
  CAST("encounter_start_time" AS TIMESTAMPTZ) DESC NULLS LAST;
