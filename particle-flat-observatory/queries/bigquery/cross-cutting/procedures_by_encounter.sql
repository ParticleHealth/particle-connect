-- =============================================================================
-- Query: Procedures by Encounter
-- Requirement: CROSS-03
-- Dialect: BigQuery
-- Description: Joins procedures to encounters and practitioners. Uses the direct
--              encounter_reference_id foreign key when available. Also joins to
--              practitioners via performer_practitioner_role_reference_id.
--
--              Note: encounter_reference_id is NULL for all procedures in sample
--              data. When populated, this join will link procedures to their
--              encounters. A temporal join alternative is provided below for
--              cases where the FK is NULL but timestamps overlap.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE `patient_id` = @patient_id
-- Tables used: procedures, encounters, practitioners
-- =============================================================================

WITH
  procedure_details AS (
    SELECT
      `procedure_id`,
      `procedure_name`,
      `procedure_code`,
      `procedure_reason`,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `procedure_date_time`) AS procedure_ts,
      `encounter_reference_id`,
      `performer_practitioner_role_reference_id`,
      `patient_id`
    FROM procedures
    WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  encounter_details AS (
    SELECT
      `encounter_id`,
      `encounter_type_name`,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_start_time`) AS start_ts,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_end_time`)   AS end_ts
    FROM encounters
    WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  practitioner_details AS (
    SELECT
      `practitioner_role_id`,
      `practitioner_given_name`,
      `practitioner_family_name`,
      `practitioner_role_specialty`
    FROM practitioners
    WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  )

-- Direct FK join (encounter_reference_id) + practitioner join
SELECT
  pd.`procedure_id`,
  pd.`procedure_name`,
  pd.`procedure_code`,
  pd.`procedure_reason`,
  pd.procedure_ts,
  ed.`encounter_id`,
  ed.`encounter_type_name`,
  ed.start_ts                          AS encounter_start,
  ed.end_ts                            AS encounter_end,
  CONCAT(prd.`practitioner_given_name`, ' ', prd.`practitioner_family_name`) AS practitioner_name,
  prd.`practitioner_role_specialty`
FROM procedure_details pd
LEFT JOIN encounter_details ed
  ON pd.`encounter_reference_id` = ed.`encounter_id`
LEFT JOIN practitioner_details prd
  ON pd.`performer_practitioner_role_reference_id` = prd.`practitioner_role_id`
ORDER BY pd.procedure_ts DESC NULLS LAST;


-- =============================================================================
-- Alternative: Temporal join for procedures without encounter_reference_id
--
-- When encounter_reference_id is NULL (as in sample data), this alternative
-- matches procedures to encounters using timestamp overlap, similar to the
-- labs_by_encounter approach. Uncomment to use.
-- =============================================================================

-- WITH
--   procedure_details AS (
--     SELECT
--       `procedure_id`,
--       `procedure_name`,
--       `procedure_code`,
--       `procedure_reason`,
--       PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `procedure_date_time`) AS procedure_ts,
--       `performer_practitioner_role_reference_id`,
--       `patient_id`
--     FROM procedures
--     WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'
--       AND `procedure_date_time` IS NOT NULL
--   ),
--   encounter_details AS (
--     SELECT
--       `encounter_id`,
--       `encounter_type_name`,
--       PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_start_time`) AS start_ts,
--       PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_end_time`)   AS end_ts,
--       `patient_id`
--     FROM encounters
--     WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'
--       AND `encounter_start_time` IS NOT NULL
--       AND `encounter_end_time` IS NOT NULL
--   ),
--   practitioner_details AS (
--     SELECT
--       `practitioner_role_id`,
--       `practitioner_given_name`,
--       `practitioner_family_name`,
--       `practitioner_role_specialty`
--     FROM practitioners
--     WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'
--   )
-- SELECT
--   pd.`procedure_name`,
--   pd.`procedure_code`,
--   pd.procedure_ts,
--   ed.`encounter_id`,
--   ed.`encounter_type_name`,
--   ed.start_ts AS encounter_start,
--   ed.end_ts   AS encounter_end,
--   CONCAT(prd.`practitioner_given_name`, ' ', prd.`practitioner_family_name`) AS practitioner_name,
--   prd.`practitioner_role_specialty`
-- FROM procedure_details pd
-- INNER JOIN encounter_details ed
--   ON pd.`patient_id` = ed.`patient_id`
--   AND pd.procedure_ts BETWEEN ed.start_ts AND ed.end_ts
-- LEFT JOIN practitioner_details prd
--   ON pd.`performer_practitioner_role_reference_id` = prd.`practitioner_role_id`
-- ORDER BY pd.procedure_ts DESC NULLS LAST;
