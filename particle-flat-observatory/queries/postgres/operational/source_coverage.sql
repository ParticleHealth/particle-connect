-- =============================================================================
-- Query: Source Coverage Breakdown
-- Requirement: OPS-02
-- Dialect: PostgreSQL
-- Description: Shows which data sources contributed records and to which
--              resource types. Answers: "Where did my data come from, and
--              what did each source provide?"
-- Parameters: none (global query)
-- Tables used: record_sources, sources
-- =============================================================================

WITH resource_type_totals AS (
  SELECT
    "resource_type",
    COUNT(*) AS total_for_type
  FROM "record_sources"
  GROUP BY "resource_type"
)
SELECT
  s."source_name",
  rs."resource_type",
  COUNT(*) AS record_count,
  ROUND(100.0 * COUNT(*) / NULLIF(t.total_for_type, 0), 1) AS pct_of_type
FROM "record_sources" rs
INNER JOIN "sources" s
  ON rs."source_id" = s."source_id"
INNER JOIN resource_type_totals t
  ON rs."resource_type" = t."resource_type"
GROUP BY s."source_name", rs."resource_type", t.total_for_type
ORDER BY s."source_name", record_count DESC;
