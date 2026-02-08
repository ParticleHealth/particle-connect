-- =============================================================================
-- Query: Record Freshness
-- Requirement: OPS-03
-- Dialect: PostgreSQL
-- Description: Shows the most recent record timestamp per resource type.
--              Answers: "How fresh is my data? When was each resource type
--              last updated?"
-- Parameters: none (global query)
-- Tables used: encounters, problems, medications, labs, vital_signs,
--              procedures, ai_outputs, transitions, patients, practitioners,
--              organizations, locations, document_references, sources,
--              record_sources, ai_citations
-- =============================================================================

SELECT
  resource_type,
  record_count,
  most_recent
FROM (
  -- Tables WITH timestamp columns
  SELECT
    'encounters' AS resource_type,
    COUNT(*) AS record_count,
    MAX(CAST("encounter_start_time" AS TIMESTAMPTZ)) AS most_recent
  FROM encounters

  UNION ALL
  SELECT
    'problems',
    COUNT(*),
    MAX(CAST("condition_onset_date" AS TIMESTAMPTZ))
  FROM problems

  UNION ALL
  SELECT
    'medications',
    COUNT(*),
    MAX(CAST("medication_statement_start_time" AS TIMESTAMPTZ))
  FROM medications

  UNION ALL
  SELECT
    'labs',
    COUNT(*),
    MAX(CAST("lab_timestamp" AS TIMESTAMPTZ))
  FROM labs

  UNION ALL
  SELECT
    'vital_signs',
    COUNT(*),
    MAX(CAST(LTRIM("vital_sign_observation_time", ', ') AS TIMESTAMPTZ))
  FROM vital_signs

  UNION ALL
  SELECT
    'procedures',
    COUNT(*),
    MAX(CAST("procedure_date_time" AS TIMESTAMPTZ))
  FROM procedures

  UNION ALL
  SELECT
    'ai_outputs',
    COUNT(*),
    MAX(CAST("created" AS TIMESTAMPTZ))
  FROM ai_outputs

  UNION ALL
  SELECT
    'transitions',
    COUNT(*),
    MAX(CAST("status_date_time" AS TIMESTAMPTZ))
  FROM transitions

  -- Tables WITHOUT timestamp columns
  UNION ALL
  SELECT 'patients', COUNT(*), NULL::TIMESTAMPTZ FROM patients

  UNION ALL
  SELECT 'practitioners', COUNT(*), NULL::TIMESTAMPTZ FROM practitioners

  UNION ALL
  SELECT 'organizations', COUNT(*), NULL::TIMESTAMPTZ FROM organizations

  UNION ALL
  SELECT 'locations', COUNT(*), NULL::TIMESTAMPTZ FROM locations

  UNION ALL
  SELECT 'document_references', COUNT(*), NULL::TIMESTAMPTZ FROM document_references

  UNION ALL
  SELECT 'sources', COUNT(*), NULL::TIMESTAMPTZ FROM sources

  UNION ALL
  SELECT 'record_sources', COUNT(*), NULL::TIMESTAMPTZ FROM record_sources

  UNION ALL
  SELECT 'ai_citations', COUNT(*), NULL::TIMESTAMPTZ FROM ai_citations
) AS freshness
ORDER BY most_recent DESC NULLS LAST;
