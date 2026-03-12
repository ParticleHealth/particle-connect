-- =============================================================================
-- Query: Care Team
-- Dialect: SQLite
-- Description: Practitioners involved in a patient's care with their
--              specialty, organization, and contact info.
-- Parameters: :patient_id
-- Tables: practitioners
-- =============================================================================

SELECT
  "practitioner_role_id",
  "practitioner_given_name" || ' ' || "practitioner_family_name" AS provider_name,
  "practitioner_specialty" AS specialty,
  "practitioner_role_code_name" AS role,
  "organization_name",
  "practitioner_phone" AS phone,
  "practitioner_address_city" AS city,
  "practitioner_address_state" AS state
FROM practitioners
WHERE "_patient_id" = :patient_id
ORDER BY "practitioner_specialty", "practitioner_family_name";
