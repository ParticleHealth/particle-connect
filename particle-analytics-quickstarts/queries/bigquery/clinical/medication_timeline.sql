-- =============================================================================
-- Query: Medication Timeline
-- Requirement: CLIN-03
-- Dialect: BigQuery
-- Description: Returns all medications for a patient with start/end dates,
--              dosage information, and computed duration. Shows a chronological
--              view of medication history.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE patient_id = @patient_id
-- Tables used: medications
-- =============================================================================

SELECT
  `medication_name`,
  `medication_code`,
  `medication_code_system`,
  `medication_statement_status`,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_start_time`) AS start_time,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_end_time`) AS end_time,
  CASE
    WHEN `medication_statement_start_time` IS NOT NULL
     AND `medication_statement_end_time` IS NOT NULL
    THEN TIMESTAMP_DIFF(
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_end_time`),
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_start_time`),
      DAY
    )
    ELSE NULL
  END AS duration_days,
  `medication_statement_dose_value`,
  `medication_statement_dose_unit`,
  `medication_statement_dose_route`,
  `medication_statement_patient_instructions`,
  `medication_statement_id`,
  `practitioner_role_id`
FROM medications
WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
ORDER BY
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_start_time`) DESC NULLS LAST;
