-- =============================================================================
-- Query: Record Freshness
-- Requirement: OPS-03
-- Dialect: BigQuery
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
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `encounter_start_time`)) AS most_recent
  FROM encounters

  UNION ALL
  SELECT
    'problems',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `condition_onset_date`))
  FROM problems

  UNION ALL
  SELECT
    'medications',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `medication_statement_start_time`))
  FROM medications

  UNION ALL
  SELECT
    'labs',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `lab_timestamp`))
  FROM labs

  UNION ALL
  SELECT
    'vital_signs',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', LTRIM(`vital_sign_observation_time`, ', ')))
  FROM vital_signs

  UNION ALL
  SELECT
    'procedures',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `procedure_date_time`))
  FROM procedures

  UNION ALL
  SELECT
    'ai_outputs',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', `created`))
  FROM ai_outputs

  UNION ALL
  SELECT
    'transitions',
    COUNT(*),
    MAX(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S', `status_date_time`))
  FROM transitions

  -- Tables WITHOUT timestamp columns
  UNION ALL
  SELECT 'patients', COUNT(*), CAST(NULL AS TIMESTAMP) FROM patients

  UNION ALL
  SELECT 'practitioners', COUNT(*), CAST(NULL AS TIMESTAMP) FROM practitioners

  UNION ALL
  SELECT 'organizations', COUNT(*), CAST(NULL AS TIMESTAMP) FROM organizations

  UNION ALL
  SELECT 'locations', COUNT(*), CAST(NULL AS TIMESTAMP) FROM locations

  UNION ALL
  SELECT 'document_references', COUNT(*), CAST(NULL AS TIMESTAMP) FROM document_references

  UNION ALL
  SELECT 'sources', COUNT(*), CAST(NULL AS TIMESTAMP) FROM sources

  UNION ALL
  SELECT 'record_sources', COUNT(*), CAST(NULL AS TIMESTAMP) FROM record_sources

  UNION ALL
  SELECT 'ai_citations', COUNT(*), CAST(NULL AS TIMESTAMP) FROM ai_citations
)
ORDER BY most_recent DESC NULLS LAST;
