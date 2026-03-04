-- =============================================================================
-- Query: Data Completeness Scorecard
-- Requirement: OPS-01
-- Dialect: PostgreSQL
-- Description: Shows record counts and key field population percentages for
--              all 16 resource types that have data. Answers: "How much data
--              do we have, and how complete is it?"
-- Parameters: none (global query)
-- Tables used: patients, encounters, problems, medications, labs, vital_signs,
--              procedures, practitioners, organizations, locations,
--              document_references, sources, record_sources, ai_outputs,
--              ai_citations, transitions
-- =============================================================================

SELECT
  resource_type,
  record_count,
  key_field_populated,
  ROUND(100.0 * key_field_populated / NULLIF(record_count, 0), 1) AS key_field_pct
FROM (
  SELECT
    'patients' AS resource_type,
    COUNT(*) AS record_count,
    COUNT("given_name") AS key_field_populated
  FROM patients

  UNION ALL
  SELECT
    'encounters',
    COUNT(*),
    COUNT("encounter_type_name")
  FROM encounters

  UNION ALL
  SELECT
    'problems',
    COUNT(*),
    COUNT("condition_name")
  FROM problems

  UNION ALL
  SELECT
    'medications',
    COUNT(*),
    COUNT("medication_name")
  FROM medications

  UNION ALL
  SELECT
    'labs',
    COUNT(*),
    COUNT("lab_name")
  FROM labs

  UNION ALL
  SELECT
    'vital_signs',
    COUNT(*),
    COUNT("vital_sign_observation_name")
  FROM vital_signs

  UNION ALL
  SELECT
    'procedures',
    COUNT(*),
    COUNT("procedure_name")
  FROM procedures

  UNION ALL
  SELECT
    'practitioners',
    COUNT(*),
    COUNT("practitioner_given_name")
  FROM practitioners

  UNION ALL
  SELECT
    'organizations',
    COUNT(*),
    COUNT("organization_name")
  FROM organizations

  UNION ALL
  SELECT
    'locations',
    COUNT(*),
    COUNT("location_name")
  FROM locations

  UNION ALL
  SELECT
    'document_references',
    COUNT(*),
    COUNT("document_reference_type")
  FROM document_references

  UNION ALL
  SELECT
    'sources',
    COUNT(*),
    COUNT("source_name")
  FROM sources

  UNION ALL
  SELECT
    'record_sources',
    COUNT(*),
    COUNT("resource_id")
  FROM record_sources

  UNION ALL
  SELECT
    'ai_outputs',
    COUNT(*),
    COUNT("type")
  FROM ai_outputs

  UNION ALL
  SELECT
    'ai_citations',
    COUNT(*),
    COUNT("resource_reference_id")
  FROM ai_citations

  UNION ALL
  SELECT
    'transitions',
    COUNT(*),
    COUNT("facility_name")
  FROM transitions
) AS completeness
ORDER BY record_count DESC;
