-- =============================================================================
-- Query: Encounter Timeline
-- Dialect: SQLite
-- Description: Chronological view of patient encounters (visits) with type,
--              facility, date range, and associated conditions/practitioners.
-- Parameters: :patient_id
-- Tables: encounters
-- =============================================================================

SELECT
  "encounter_id",
  "encounter_type_name" AS visit_type,
  "encounter_class" AS visit_class,
  "encounter_status",
  "encounter_start_date" AS start_date,
  "encounter_end_date" AS end_date,
  "facility_name",
  "facility_type",
  "condition_id_references" AS related_conditions,
  "practitioner_role_id_references" AS related_practitioners
FROM encounters
WHERE "_patient_id" = :patient_id
ORDER BY "encounter_start_date" DESC;
