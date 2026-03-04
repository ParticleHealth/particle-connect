-- =============================================================================
-- Query: Data Provenance
-- Requirement: OPS-04
-- Dialect: BigQuery
-- Description: Traces clinical records back to their originating data sources
--              via the record_sources and sources tables. Answers: "Which
--              sources contributed data for this patient, and what did each
--              source provide?"
-- Parameters: patient_id (scoped to a single patient)
-- Tables used: record_sources, sources
-- =============================================================================

-- Replace the patient_id below with the target patient
-- Parameterized: WHERE rs.`patient_id` = @patient_id

-- -----------------------------------------------------------------------
-- Summary: source contribution by resource type
-- -----------------------------------------------------------------------
SELECT
  rs.`resource_type`,
  COUNT(DISTINCT s.`source_name`) AS distinct_sources,
  COUNT(*) AS record_count
FROM `record_sources` rs
INNER JOIN `sources` s
  ON rs.`source_id` = s.`source_id`
WHERE rs.`patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'
GROUP BY rs.`resource_type`
ORDER BY record_count DESC;

-- -----------------------------------------------------------------------
-- Detail: full provenance trace
-- -----------------------------------------------------------------------
SELECT
  rs.`resource_type`,
  rs.`resource_id`,
  rs.`resource_id_name`,
  s.`source_name`
FROM `record_sources` rs
INNER JOIN `sources` s
  ON rs.`source_id` = s.`source_id`
WHERE rs.`patient_id` = '6f3bc061-8515-41b9-bc26-75fc55f53284'
ORDER BY rs.`resource_type`, rs.`resource_id`;
