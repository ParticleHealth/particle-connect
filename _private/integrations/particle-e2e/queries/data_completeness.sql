-- =============================================================================
-- Query: Data Completeness Scorecard
-- Dialect: SQLite
-- Description: Record counts per resource type, showing how much data was
--              returned by the Particle query. Runs across all tables in the
--              database to give a bird's-eye view of data volume.
-- Parameters: none (global query)
-- Tables: all resource tables
-- =============================================================================

SELECT resource_type, record_count
FROM (
  SELECT 'patients' AS resource_type, COUNT(*) AS record_count FROM patients
  UNION ALL
  SELECT 'encounters', COUNT(*) FROM encounters
  UNION ALL
  SELECT 'problems', COUNT(*) FROM problems
  UNION ALL
  SELECT 'medications', COUNT(*) FROM medications
  UNION ALL
  SELECT 'labs', COUNT(*) FROM labs
  UNION ALL
  SELECT 'vital_signs', COUNT(*) FROM vital_signs
  UNION ALL
  SELECT 'procedures', COUNT(*) FROM procedures
  UNION ALL
  SELECT 'practitioners', COUNT(*) FROM practitioners
  UNION ALL
  SELECT 'organizations', COUNT(*) FROM organizations
  UNION ALL
  SELECT 'locations', COUNT(*) FROM locations
  UNION ALL
  SELECT 'document_references', COUNT(*) FROM document_references
  UNION ALL
  SELECT 'sources', COUNT(*) FROM sources
  UNION ALL
  SELECT 'record_sources', COUNT(*) FROM record_sources
  UNION ALL
  SELECT 'ai_outputs', COUNT(*) FROM ai_outputs
  UNION ALL
  SELECT 'ai_citations', COUNT(*) FROM ai_citations
  UNION ALL
  SELECT 'transitions', COUNT(*) FROM transitions
)
ORDER BY record_count DESC;
