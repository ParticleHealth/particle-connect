-- =============================================================================
-- Query: Lab Results
-- Dialect: SQLite
-- Description: Lab observations with values, units, reference ranges, and
--              interpretation flags. Ordered by most recent collection date.
-- Parameters: :patient_id
-- Tables: labs
-- =============================================================================

SELECT
  "lab_name",
  "lab_code",
  "lab_code_system",
  "lab_value" AS result_value,
  "lab_value_unit" AS result_unit,
  "lab_reference_range",
  "lab_interpretation",
  "lab_status",
  "lab_collection_date" AS collection_date,
  "lab_issued_date" AS issued_date,
  "encounter_id"
FROM labs
WHERE "_patient_id" = :patient_id
ORDER BY "lab_collection_date" DESC;
