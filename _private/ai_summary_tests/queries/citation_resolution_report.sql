-- =============================================================================
-- Query: Citation Resolution Report
-- Dialect: SQLite
-- Description: For each AI output, shows how many citations resolve to source
--              documents vs. how many are orphaned. Measures the "verifiability"
--              of each summary from flat data alone.
-- Tables: aIOutputs, aICitations, documentReferences, labs, encounters
-- =============================================================================

SELECT
    o.ai_output_id,
    o.type AS summary_type,
    COUNT(c.citation_id) AS total_citations,
    COUNT(DISTINCT c.resource_reference_id) AS unique_sources,

    -- DocumentReference citations
    SUM(CASE WHEN c.resource_type = 'DocumentReferences' THEN 1 ELSE 0 END) AS doc_citations,
    SUM(CASE WHEN c.resource_type = 'DocumentReferences'
              AND d.document_reference_id IS NOT NULL THEN 1 ELSE 0 END) AS doc_resolved,
    SUM(CASE WHEN c.resource_type = 'DocumentReferences'
              AND d.document_reference_id IS NULL THEN 1 ELSE 0 END) AS doc_orphaned,

    -- Structured citations (Labs, Encounters, etc.)
    SUM(CASE WHEN c.resource_type != 'DocumentReferences' THEN 1 ELSE 0 END) AS structured_citations,

    -- Resolution rate
    ROUND(100.0 *
        (SUM(CASE WHEN c.resource_type = 'DocumentReferences'
                   AND d.document_reference_id IS NOT NULL THEN 1 ELSE 0 END)
         + SUM(CASE WHEN c.resource_type != 'DocumentReferences' THEN 1 ELSE 0 END))
        / COUNT(c.citation_id), 1) AS resolution_pct

FROM aIOutputs o
INNER JOIN aICitations c ON o.ai_output_id = c.ai_output_id
LEFT JOIN documentReferences d
    ON c.resource_reference_id = d.document_reference_id
    AND c.resource_type = 'DocumentReferences'
GROUP BY o.ai_output_id, o.type
ORDER BY resolution_pct DESC;
