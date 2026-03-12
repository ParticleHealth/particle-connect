-- =============================================================================
-- Query: Active Problem List
-- Dialect: SQLite
-- Description: All conditions for a patient ordered by clinical status
--              (active first) then by onset date (most recent first).
-- Parameters: :patient_id
-- Tables: problems
-- =============================================================================

SELECT
  "condition_id",
  "condition_name",
  "condition_clinical_status",
  CASE
    WHEN "condition_clinical_status" = 'active' THEN 'Active'
    WHEN "condition_clinical_status" = 'resolved' THEN 'Resolved'
    ELSE COALESCE("condition_clinical_status", 'Unknown')
  END AS status_label,
  "condition_onset_date" AS onset_date,
  "condition_recorded_date" AS recorded_date,
  "condition_code",
  "condition_code_system",
  "condition_category_code_name" AS category,
  "condition_text",
  "encounter_id"
FROM problems
WHERE "_patient_id" = :patient_id
ORDER BY
  CASE WHEN "condition_clinical_status" = 'active' THEN 0 ELSE 1 END,
  "condition_onset_date" DESC;
