-- =============================================================================
-- Query: AI Summary with Citations
-- Dialect: SQLite
-- Description: Joins an AI output to all its citations, with source document
--              resolution where available. Shows the full evidence chain for
--              a single summary.
-- Parameters: :ai_output_id (or use the first DISCHARGE_SUMMARY if not provided)
-- Tables: aIOutputs, aICitations, documentReferences
-- =============================================================================

SELECT
    o.ai_output_id,
    o.type AS summary_type,
    c.citation_id,
    c.resource_type AS citation_source_type,
    c.text_snippet,
    c.resource_reference_id,
    d.document_reference_type AS resolved_doc_type,
    CASE
        WHEN d.document_reference_id IS NOT NULL THEN 'RESOLVED'
        WHEN c.resource_type != 'DocumentReferences' THEN 'STRUCTURED'
        ELSE 'ORPHANED'
    END AS resolution_status
FROM aIOutputs o
INNER JOIN aICitations c ON o.ai_output_id = c.ai_output_id
LEFT JOIN documentReferences d
    ON c.resource_reference_id = d.document_reference_id
    AND c.resource_type = 'DocumentReferences'
WHERE o.type = 'DISCHARGE_SUMMARY'
ORDER BY o.ai_output_id, c.resource_type, c.citation_id
LIMIT 50;
