-- =============================================================================
-- Query: AI Output Summary
-- Requirement: OPS-05
-- Dialect: PostgreSQL
-- Description: Summarizes AI-generated outputs (discharge summaries, patient
--              histories) with citation counts. Answers: "What AI content
--              exists, how many clinical records does each output cite, and
--              what resource types are referenced?"
-- Parameters: none (global query)
-- Tables used: ai_outputs, ai_citations
-- =============================================================================

WITH output_with_citations AS (
  SELECT
    ao."ai_output_id",
    ao."type",
    CAST(ao."created" AS TIMESTAMPTZ) AS created,
    LEFT(ao."text", 200) AS text_preview,
    COUNT(ac."citation_id") AS citation_count,
    COUNT(DISTINCT ac."resource_type") AS distinct_resource_types_cited
  FROM "ai_outputs" ao
  LEFT JOIN "ai_citations" ac
    ON ao."ai_output_id" = ac."ai_output_id"
  GROUP BY
    ao."ai_output_id",
    ao."type",
    ao."created",
    ao."text"
),

type_summary AS (
  SELECT
    "type",
    COUNT(*) AS output_count,
    SUM(citation_count) AS total_citations,
    ROUND(AVG(citation_count), 1) AS avg_citations_per_output
  FROM output_with_citations
  GROUP BY "type"
)

-- Per-output detail
SELECT
  'detail' AS section,
  oc."ai_output_id",
  oc."type",
  oc.created,
  oc.text_preview,
  oc.citation_count,
  oc.distinct_resource_types_cited,
  NULL::BIGINT AS output_count,
  NULL::BIGINT AS total_citations,
  NULL::NUMERIC AS avg_citations_per_output
FROM output_with_citations oc

UNION ALL

-- Type-level summary
SELECT
  'summary',
  NULL,
  ts."type",
  NULL,
  NULL,
  NULL::BIGINT,
  NULL::BIGINT,
  ts.output_count,
  ts.total_citations,
  ts.avg_citations_per_output
FROM type_summary ts

ORDER BY section, created DESC;
