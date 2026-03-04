-- =============================================================================
-- Query: Care Team
-- Requirement: CLIN-07
-- Dialect: PostgreSQL
-- Description: Returns all practitioners involved in a patient's care, gathered
--              from three sources: encounters (via comma-separated
--              practitioner_role_id_references), medications (via direct
--              practitioner_role_id FK), and procedures (via
--              performer_practitioner_role_reference_id). Each source is labeled
--              with a relationship column.
-- Parameters: patient_id = '6f3bc061-8515-41b9-bc26-75fc55f53284' (replace with your patient_id)
-- Parameterized: WHERE "patient_id" = :patient_id
-- Tables used: practitioners, encounters, medications, procedures
-- =============================================================================

WITH
  -- Source 1: Practitioners from encounters (comma-separated field)
  encounter_practitioners AS (
    SELECT
      unnest(string_to_array("practitioner_role_id_references", ', ')) AS practitioner_role_id,
      "encounter_id",
      "encounter_type_name",
      'encounter' AS relationship
    FROM encounters
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND "practitioner_role_id_references" IS NOT NULL
  ),

  -- Source 2: Practitioners from medications (direct FK)
  medication_practitioners AS (
    SELECT
      "practitioner_role_id",
      "medication_statement_id" AS reference_id,
      "medication_name" AS reference_name,
      'medication' AS relationship
    FROM medications
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND "practitioner_role_id" IS NOT NULL
  ),

  -- Source 3: Practitioners from procedures (direct FK)
  procedure_practitioners AS (
    SELECT
      "performer_practitioner_role_reference_id" AS practitioner_role_id,
      "procedure_id" AS reference_id,
      "procedure_name" AS reference_name,
      'procedure' AS relationship
    FROM procedures
    WHERE "patient_id" = '6f3bc061-8515-41b9-bc26-75fc55f53284'  -- Replace with your patient_id
      AND "performer_practitioner_role_reference_id" IS NOT NULL
  ),

  -- Combine all practitioner references
  all_references AS (
    SELECT practitioner_role_id, encounter_id AS reference_id, encounter_type_name AS reference_name, relationship
    FROM encounter_practitioners
    UNION ALL
    SELECT practitioner_role_id, reference_id, reference_name, relationship
    FROM medication_practitioners
    UNION ALL
    SELECT practitioner_role_id, reference_id, reference_name, relationship
    FROM procedure_practitioners
  )

SELECT DISTINCT
  p."practitioner_given_name",
  p."practitioner_family_name",
  p."practitioner_name_suffix",
  p."practitioner_role",
  p."practitioner_role_specialty",
  p."practitioner_role_id",
  ar.relationship,
  ar.reference_id,
  ar.reference_name
FROM all_references ar
INNER JOIN practitioners p
  ON ar.practitioner_role_id = p."practitioner_role_id"
ORDER BY
  p."practitioner_family_name",
  p."practitioner_given_name",
  ar.relationship;
