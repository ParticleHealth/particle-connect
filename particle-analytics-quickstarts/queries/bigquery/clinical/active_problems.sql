-- =============================================================================
-- Query: Active Problem List
-- Requirement: CLIN-02
-- Dialect: BigQuery
-- Description: Returns all conditions (problems) for a patient with their
--              clinical status, onset date, and coding. Shows both active and
--              resolved conditions, ordered by most recent onset first.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE patient_id = @patient_id
-- Tables used: problems
-- =============================================================================

SELECT
  `condition_id`,
  `condition_name`,
  `condition_clinical_status`,
  CASE
    WHEN `condition_clinical_status` = 'active' THEN 'Active'
    WHEN `condition_clinical_status` = 'resolved' THEN 'Resolved'
    ELSE COALESCE(`condition_clinical_status`, 'Unknown')
  END AS status_label,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `condition_onset_date`) AS onset_date,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `condition_recorded_date`) AS recorded_date,
  `condition_code`,
  `condition_code_system`,
  `condition_category_code_name` AS category,
  `condition_text`,
  `encounter_id`
FROM problems
WHERE `patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
ORDER BY
  CASE WHEN `condition_clinical_status` = 'active' THEN 0 ELSE 1 END,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `condition_onset_date`) DESC NULLS LAST;
