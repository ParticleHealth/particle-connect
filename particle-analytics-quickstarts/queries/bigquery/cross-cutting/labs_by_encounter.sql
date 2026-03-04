-- =============================================================================
-- Query: Labs by Encounter
-- Requirement: CROSS-01
-- Dialect: BigQuery
-- Description: Associates lab results with encounters using temporal overlap.
--              Labs have NO encounter foreign key in Particle flat data, so this
--              query matches labs to encounters where the lab timestamp falls
--              within the encounter's start and end time window.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE `patient_id` = @patient_id
-- Tables used: labs, encounters
-- =============================================================================

WITH
  -- Parse encounter timestamps and filter to those with valid time windows
  parsed_encounters AS (
    SELECT
      `encounter_id`,
      `encounter_type_name`,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_start_time`) AS start_ts,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_end_time`)   AS end_ts,
      `patient_id`
    FROM encounters
    WHERE `encounter_start_time` IS NOT NULL
      AND `encounter_end_time` IS NOT NULL
      AND `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  ),

  -- Parse lab timestamps
  parsed_labs AS (
    SELECT
      `lab_observation_id`,
      `lab_name`,
      `lab_code`,
      `lab_value_quantity`,
      `lab_unit`,
      `lab_interpretation`,
      `diagnostic_report_name`,
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `lab_timestamp`) AS lab_ts,
      `patient_id`
    FROM labs
    WHERE `lab_timestamp` IS NOT NULL
      AND `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
  )

-- Temporal join: match labs to encounters where the lab occurred during the encounter
SELECT
  pe.`encounter_id`,
  pe.`encounter_type_name`,
  pe.start_ts                          AS encounter_start,
  pe.end_ts                            AS encounter_end,
  pl.`lab_observation_id`,
  pl.`lab_name`,
  pl.`lab_code`,
  SAFE_CAST(pl.`lab_value_quantity` AS FLOAT64) AS value_numeric,
  pl.`lab_unit`,
  pl.`lab_interpretation`,
  pl.`diagnostic_report_name`,
  pl.lab_ts                            AS lab_timestamp
FROM parsed_encounters pe
INNER JOIN parsed_labs pl
  ON pe.`patient_id` = pl.`patient_id`
  AND pl.lab_ts BETWEEN pe.start_ts AND pe.end_ts
ORDER BY pe.start_ts, pl.lab_ts;
